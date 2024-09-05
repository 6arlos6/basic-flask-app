from .entities.User import User
from werkzeug.security import generate_password_hash
#import unidecode
import pandas as pd
from unidecode import unidecode

class ModelUser():

    @classmethod
    def login(self, db, user):
        try:
            cursor = db.connection.cursor()
            sql = """SELECT id, username, password, fullname, rol, fecha_modificacion
                     FROM user_rol
                     WHERE username = '{}'""".format(user.username)
            cursor.execute(sql)
            row = cursor.fetchone()
            if row != None:
                
                user = User(row[0], row[1], User.check_password(row[2], user.password), row[3], row[4], row[5])
                return user
            else:
                return None
        except Exception as ex:
            raise Exception(ex)

    @classmethod
    def get_by_id(self, db, id):
        try:
            cursor = db.connection.cursor()
            sql = "SELECT id, username, fullname, rol, fecha_modificacion FROM user_rol WHERE id = {}".format(id)
            cursor.execute(sql)
            row = cursor.fetchone()
            if row != None:
                return User(row[0], row[1], None, row[2], row[3])
            else:
                return None
        except Exception as ex:
            raise Exception(ex)
    
    # Clase de modificacion de fecha:
    @classmethod
    def update_date(self, db, id, date):
        try:
            cursor = db.connection.cursor()
            #sql = "SELECT id, username, fullname, rol FROM user_rol WHERE id = {}".format(id)
            sql = "UPDATE user_rol SET fecha_modificacion = '{}' WHERE ID = {}".format(date, id)
            print("SQLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL")
            print(sql)
            cursor.execute(sql)
            db.connection.commit()
            return 'exito'
        except Exception as ex:
            raise Exception(ex)

    # Get date:
    @classmethod
    def get_date_modf(self, db, id):
        try:
            cursor = db.connection.cursor()
            sql = "SELECT fecha_modificacion FROM user_rol WHERE id = {}".format(id)
            cursor.execute(sql)
            row = cursor.fetchone()
            if row != None:
                return row[0]
            else:
                return None
        except Exception as ex:
            raise Exception(ex)
    # API:
    '''
    @classmethod
    def upload_df(self, db, df, table):
        try:
            # dataframe:
            cols = list(df.columns)
            n_cols = len(cols)
            # coneccion:
            cursor = db.connection.cursor()
            #query_RESET = f'ALTER TABLE {table} AUTO_INCREMENT = 1'
            query = f'INSERT INTO {table}\n'
            val_list = ["%s" for i in range(n_cols-1)]
            val_list_str = ", ".join(val_list)
            query += 'VALUES(' + val_list_str + ')\n'
            print("===========================================")
            print(query)
            # Delete duplicates:
            sql_del = f"DELETE t1 FROM {table} t1\n"
            sql_del += f"INNER JOIN {table} t2\n" 
            sql_del += "WHERE\n"
            #sql_del += f"   t1.ID < t2.ID AND\n"
            for i in range(len(cols)-1):
                sql_del += f"   t1.{cols[i]} = t2.{cols[i]} AND\n"
            sql_del += f"   t1.{cols[i+1]} = t2.{cols[i+1]}"
            
            # dummy_non_duplicate_table
            #query = 'INSERT ignore into db1 VALUES(%s, %s, %s, %s)'
            my_data = []
            # formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')
            for i_row in range(len(df)):
                row = list(df.iloc[i_row,:])
                row = [str(e) for e in row]
                row = tuple(row)
                #print(row)
                my_data.append(row)
            #print(my_data)
            #cursor.execute(query_RESET)
            cursor.executemany(query, my_data)
            cursor.execute(sql_del)
            db.connection.commit()
            return 'exito'
        except Exception as ex:
            raise Exception(ex)
        '''
    
    @classmethod
    def upload_df(self, db, df, table):
        #try:
            # dataframe:
        print("=============== COLUMNA  ANTES ==============")
        print(list(df.columns))
        cols = list(df.columns)
        #cols_tupl = set([col.replace('-','_') for col in cols]) # OJO
        cols_tupl = [col.replace('-','_') for col in cols]
        cols_tupl = [col.replace(' ','_') for col in cols_tupl]
        cols_tupl = [unidecode(col) for col in cols_tupl]
        print("=============== COLUMNA  Despues de poner _ ==============")
        print(cols_tupl)
        df.columns = list(cols_tupl)
        n_cols = len(cols_tupl)
        print("=============== COLUMNA ==============")
        print(cols_tupl , len(cols_tupl))
        cols_estr_valu = '(' + ", ".join(cols_tupl) + ')'
        # coneccion:
        cursor = db.connection.cursor()
        query = f'INSERT INTO {table}' + cols_estr_valu + '\n'
        val_list = ['%s' for i in range(n_cols)]
        val_list_str = ", ".join(val_list)
        query += 'VALUES(' + val_list_str + ')\n'
        print("===========================================")
        print(query)
        my_data = []
        for index, row_i in df.iterrows():
            row = []
            for c in cols_tupl:
                row.append(row_i[c])
                if index == 0:
                    print(c)
            row = [unidecode(str(e)) for e in row]
            row = tuple(row)
            my_data.append(row)
        #query2 = f"DELETE FROM {table}"
        query3 = f"alter table {table} AUTO_INCREMENT = 1"
        #cursor.execute(query2)
        cursor.execute(query3)
        cursor.executemany(query, my_data)
        db.connection.commit()
        return 'exito'
        #except Exception as ex:
        #    raise Exception(ex)

    @classmethod
    def get_distinct(self, db, table):
        # sirve para mostar los valores distintos en funcion de USER y fecha de actualizacion
        # en la tabla.
        try:
            cursor = db.connection.cursor()
            # ALTER TABLE tablename AUTO_INCREMENT = 1
            query = f'SELECT DISTINCT DATE_UPDATE, USER FROM {table}'  
            cursor.execute(query)
            records = cursor.fetchall()
            print("Total number of rows in table: ", cursor.rowcount)

            DATE = []
            USER = []
            ID = []
            for id,row in enumerate(records):
                first = row[0]
                last_name = row[1]
                DATE.append(first)
                USER.append(last_name)
                ID.append(id)
            df = pd.DataFrame(
                {   
                    'ID':ID,
                    'DATE':DATE,
                    'USER':USER
                }
            )
            return df
        except Exception as ex:
            raise Exception(ex)
    
    @classmethod
    def get_distinct_V2(self, db, table):
        # sirve para mostar los valores distintos en funcion de USER y fecha de actualizacion
        # en la tabla.
        try:
            cursor = db.connection.cursor()
            # ALTER TABLE tablename AUTO_INCREMENT = 1
            # SELECT USER, DATE_UPDATE, COUNT(*) AS cantidad FROM acmp_1 GROUP BY USER, DATE_UPDATE;
            query = f'SELECT USER, DATE_UPDATE, COUNT(*) AS cantidad FROM {table} GROUP BY USER, DATE_UPDATE'  
            cursor.execute(query)
            records = cursor.fetchall()
            print("Total number of rows in table: ", cursor.rowcount)
            USER = []
            DATE = []
            COUNT = []
            for id,row in enumerate(records):
                user = row[0]
                date = row[1]
                count = row[2]
                USER.append(user)
                DATE.append(date)
                COUNT.append(count)
            df = pd.DataFrame(
                {   
                    'COUNT':COUNT,
                    'USER':USER,
                    'DATE':DATE
                }
            )
            return df
        except Exception as ex:
            raise Exception(ex)
    
    @classmethod
    def delete(self, db, table, user, date):
        try:
            cursor = db.connection.cursor()
            query = f'''
            DELETE FROM {table}
            WHERE USER = '{user}'
            AND DATE_UPDATE = '{date}'
            '''
            cursor.execute(query)
            db.connection.commit()

        except Exception as ex:
            raise Exception(ex)
    
    # downloa_upload:
    @classmethod
    def download_upload(self, db, table, user, date):
        try:
            cursor = db.connection.cursor()
            #query = f'''
            #DELETE FROM {table}
            #WHERE USER = '{user}'
            #AND DATE_UPDATE = '{date}'
            #'''
            query = f'''
            SELECT *
            FROM {table}
            WHERE USER = '{user}'
            AND DATE_UPDATE = '{date}'
            '''
            cursor.execute(query)
            records = cursor.fetchall()
            print("Total number of rows in table: ", cursor.rowcount)
            column_names = [desc[0] for desc in cursor.description]
            print(column_names)
            data_fetch = []
            for ind, row in enumerate(records):
                r = [row[i] for i in range(0,len(row))]
                data_fetch.append(r)
            print(len(column_names),len(list(row)))
            df = pd.DataFrame(data_fetch, columns=column_names)
            print(len(df))
            #db.connection.commit()
            return df

        except Exception as ex:
            raise Exception(ex)

    @classmethod
    def get_all_table(self, db, table, report = 'update'):
        try:
            # conecto:
            cursor = db.connection.cursor()
            # Selecciono todo:
            query = f'SELECT * FROM {table}'
            # Ejecuto:
            cursor.execute(query)
            # Obtento records:
            records = cursor.fetchall()
            # Muestro el total de filas:
            print("Total number of rows in table: ", cursor.rowcount)
            # Numero de columnas:
            columns = cursor.description
            num_fields = len(columns)
            print("Numero de columnas antes de borrar las ultimas 3: ", num_fields)
            cols_to_df = [column[0] for column in columns]
            
            if report == 'update':
                del cols_to_df[-3:]
            elif report == 'delete_sede':
                # Solo borrar  	USER 	DATE_UPDATE:
                del cols_to_df[-2:]
            
            print("COLUMNAS:")
            print(cols_to_df)
            # genero lista vacia para guardar datos:
            data = []
            # si hay datos...
            if len(records) != 0:
                print("Hay datos en historico from SQL database!")
                for row in records:
                    row = list(row)
                    # borro: ID, USER y DATE_UPDATE:
                    # del row[-3:]
                    if report == 'update':
                        del row[-3:]
                    elif report == 'delete_sede':
                        # Solo borrar  	USER 	DATE_UPDATE:
                       del row[-2:]
                    # guardar en data:
                    data.append(row)
                print(f"Numero de columnas despues de borrar lass 3 ultimas = {len(row)}")
            else:
                print("No hay datos en SQL de historico:")
                
                if report == 'update':
                    data = [[] for i in range(num_fields-3)]
                elif report == 'delete_sede':
                    # Solo borrar  	USER 	DATE_UPDATE:
                    data = [[] for i in range(num_fields-2)]
                
            print("Cantidad de datos (filas):")
            print(len(data))
            # crear dataframe vacia:
            pdd = pd.DataFrame()
            # transponer los datos:
            tlist = list(zip(*data))
            #print(len(tlist), len(tlist[0]))
            #print(tlist)
            print(len(data))
            #print(data)
            if len(tlist) != 0:
                df = pd.DataFrame(data, columns = cols_to_df)
            else:
                df = pd.DataFrame()
            print(df.info())
            return df

        except Exception as ex:
            raise Exception(ex)

class ModelAdmin():
    @classmethod
    def create(selft, db, username, password, fullname, rol, date_mod):
        try:
            cursor = db.connection.cursor()
            pass_h = generate_password_hash(password)
            sql = """INSERT INTO user_rol (username, password, fullname, rol) 
                VALUES ('{0}', '{1}', '{2}','{3}')""".format(username, pass_h, fullname, rol)
            cursor.execute(sql)
            db.connection.commit()
            return 'exito'
        except Exception as ex:
            raise Exception(ex) 
    @classmethod
    def hash_pass(self, password_str):
        pass_hash = generate_password_hash(password_str)