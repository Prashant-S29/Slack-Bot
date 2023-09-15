# Using AWS dynamodb
import boto3
db = boto3.resource("dynamodb")

all_tables = list(db.tables.all())
print(all_tables)

table = db.Table("standup_data")

print(table.table_status)

def store_data(data):
    try:
        table.put_item(
            Item=data
        )
        print("Data stored successfully")
    except Exception as e:
        print("Error")
        print(e)
    print(data)




# def send_data(data):
