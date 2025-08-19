import sqlite3
import pandas as pd
import argparse

def copy_persona(src_db, persona_id, count, dst_db):
    # 1. 从源库读取指定id的数据
    with sqlite3.connect(src_db) as src_conn:
        query = f'SELECT * FROM persona WHERE id={persona_id}'
        df = pd.read_sql_query(query, src_conn)
        if df.empty:
            raise ValueError(f'源库 {src_db} 未找到id={persona_id}的数据')
        row = df.iloc[0]

    # 2. 生成N条数据
    rows_to_insert = []
    for _ in range(count):
        new_row = row.copy()
        # id 字段设为None，让sqlite自增
        if 'id' in new_row:
            new_row['id'] = None
        rows_to_insert.append(new_row)

    # 3. 插入到目标库
    with sqlite3.connect(dst_db) as dst_conn:
        # Ensure the persona table exists in the destination
        try:
            with sqlite3.connect(src_db) as src_conn_for_schema:
                schema_query = "SELECT sql FROM sqlite_master WHERE type='table' AND name='persona'"
                create_table_sql = src_conn_for_schema.cursor().execute(schema_query).fetchone()[0]
                # Make it safe to run even if the table already exists
                create_table_sql_if_not_exists = create_table_sql.replace("CREATE TABLE", "CREATE TABLE IF NOT EXISTS")
                dst_conn.cursor().execute(create_table_sql_if_not_exists)
                dst_conn.commit()
        except Exception as e:
            raise RuntimeError(f"Could not create 'persona' table in destination DB. Error: {e}")

        cursor = dst_conn.cursor()
        cursor.execute('PRAGMA table_info(persona)')
        db_cols_with_id = [info[1] for info in cursor.fetchall()]
        # Exclude the 'id' column to allow auto-increment
        db_cols = [col for col in db_cols_with_id if col.lower() != 'id']

        final_rows = []
        for r in rows_to_insert:
            r_dict = r.to_dict()
            # Build tuple based on columns without 'id'
            final_rows.append(tuple(r_dict.get(col) for col in db_cols))

        cols_str = ','.join(f'"{c}"' for c in db_cols)
        qmarks = ','.join(['?'] * len(db_cols))
        sql = f'INSERT INTO persona ({cols_str}) VALUES ({qmarks})'
        
        cursor.executemany(sql, final_rows)
        dst_conn.commit()

    print(f'已成功从 {src_db} (id={persona_id}) 拷贝 {count} 条数据到 {dst_db} 的 persona 表')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='从一个数据库的persona表拷贝样本到另一个库')
    parser.add_argument('--src-db', type=str,  default='data/db/seed.db',help='源数据库文件路径')
    parser.add_argument('--id', type=int, required=True, help='要拷贝的persona记录的ID')
    parser.add_argument('--count', type=int, required=True, help='要拷贝的记录数量')
    parser.add_argument('--dst-db', type=str, default='data/db/deepseek-chat-single-poor-2-300.db', help='目标数据库文件路径')

    args = parser.parse_args()

    copy_persona(args.src_db, args.id, args.count, args.dst_db)