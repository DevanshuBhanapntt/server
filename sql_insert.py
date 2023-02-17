#!/usr/bin/env python
# Copyright 2019 Encore Technologies
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from st2common.runners.base_action import Action
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import URL
import decimal
import datetime

DEFAULT_KNOWN_DRIVER_CONNECTORS = {
    'postgresql': 'postgresql+psycopg2',
    'mysql': 'mysql+pymysql',
    'oracle': 'oracle+cx_oracle',
    'mssql': 'mssql+pymssql',
    'firebird': 'firebird+fdb'
}


class SQLInsert(Action):
    def __init__(self, config):
        """Creates a new Action given a StackStorm config object (kwargs works too)
        :param config: StackStorm configuration object for the pack
        :returns: a new Action
        """
        super(SQLInsert, self).__init__(config)

    def convert_timestamp(self, timestamp):
        # remove timezone overlap
        trim_timezone = timestamp.split("+")[0]
        datetime_object = datetime.datetime.strptime(trim_timezone, '%Y-%m-%d %H:%M:%S.%f')

        return datetime_object

    def row_to_dict(self, row):
        """When SQLAlchemy returns information from a query the rows are
        tuples and have some data types that need to be converted before
        being returned.
        returns: dictionary of values
        """
        return_dict = {}
        for column in row.keys():
            value = getattr(row, column)

            if isinstance(value, datetime.date):
                return_dict[column] = value.isoformat()
            elif isinstance(value, decimal.Decimal):
                return_dict[column] = float(value)
            else:
                return_dict[column] = value

        return return_dict

    def format_data(self, proc_data_obj):
        proc_data_string = ""
        if proc_data_obj:
            proc_data_list = []
            for name, value in proc_data_obj.items():
                proc_data_list.append("@{0}='{1}'".format(name, value))

            proc_data_string = ",".join(proc_data_list)

        return proc_data_string

    def build_connection(self, drivername, database, host, password, port, username):
        connection = {
            'host': host,
            'username': username,
            'password': password,
            'database': database,
            'port': port,
            'drivername': drivername
        }

        # Update Driver with a connector
        default_driver = DEFAULT_KNOWN_DRIVER_CONNECTORS.get(connection['drivername'], None)
        if default_driver:
            connection['drivername'] = default_driver

        # Format the connection string
        return URL(**connection)

    def sql_run_procedure(self, session, exec_stmt):
        return_result = None
        try:
            exec_result = session.execute(exec_stmt)

            if exec_result.returns_rows:
                return_result = []
                all_results = exec_result.fetchall()
                for row in all_results:
                    # Rows are returned as tuples with keys.
                    # Convert that to a dictionary for return
                    return_result.append(self.row_to_dict(row))
            else:
                return_result = {'affected_rows': exec_result.rowcount}

            session.commit()
        except Exception as error:
            session.rollback()

            # Return error to the user
            raise error
        finally:
            session.close()

        return return_result

    def return_details_data(self, name, value, metric_id):
        data_dict = {
            'Name': name,
            'Value': value,
            'Metric_ID': metric_id
        }

        return self.format_data(data_dict)

    def run(self,
            account_name,
            account_service,
            configuration_item,
            database,
            drivername,
            end_timestamp,
            host,
            incident_id,
            metric_data,
            metric_procedure,
            metric_detail_procedure,
            password,
            port,
            process_data,
            process_procedure,
            start_timestamp,
            username):
        start = self.convert_timestamp(start_timestamp)
        end = self.convert_timestamp(end_timestamp)
        duration = (end - start).total_seconds()
        metric_data['Start_Time'] = start.isoformat()[:-3]
        metric_data['Duration'] = duration

        database_connection_string = self.build_connection(drivername,
                                                           database,
                                                           host,
                                                           password,
                                                           port,
                                                           username)
        engine = sqlalchemy.create_engine(database_connection_string)
        session = sessionmaker(bind=engine)()

        metrics_stmt = "EXEC {} {}".format(metric_procedure, self.format_data(metric_data))
        metric_return = self.sql_run_procedure(session, metrics_stmt)
        metric_id = metric_return[0]['METRIC_ID']

        am_process_stmt = "EXEC {} {}".format(process_procedure, self.format_data(process_data))
        incident_stmt = "EXEC {} {}".format(metric_detail_procedure,
                                            self.return_details_data("Incident_ID",
                                                                     incident_id,
                                                                     metric_id))
        account_stmt = "EXEC {} {}".format(metric_detail_procedure,
                                           self.return_details_data("Account Affected",
                                                                    account_name,
                                                                    metric_id))
        item_stmt = "EXEC {} {}".format(metric_detail_procedure,
                                        self.return_details_data("Configured Item",
                                                                 configuration_item,
                                                                 metric_id))
        service_stmt = "EXEC {} {}".format(metric_detail_procedure,
                                           self.return_details_data("Account Service",
                                                                    account_service,
                                                                    metric_id))

        return_array = [metric_return[0]]
        for exec_stmt in [am_process_stmt, incident_stmt, account_stmt, item_stmt, service_stmt]:
            sql_return = self.sql_run_procedure(session, exec_stmt)
            return_value = sql_return
            if isinstance(sql_return, list):
                return_value = sql_return[0]

            return_array.append(return_value)

        return return_array
