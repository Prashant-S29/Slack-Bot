import os
from dotenv import load_dotenv
import mysql.connector
import datetime

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import logging

import database.database as dynamodb

load_dotenv()
SLACK_BOT_TOKEN = os.environ['SLACK_BOT_TOKEN']
SLACK_APP_TOKEN = os.environ['SLACK_APP_TOKEN']
MYSQL_USERNAME = os.environ['MYSQL_USERNAME']
MYSQL_PASSWORD = os.environ['MYSQL_PASSWORD']
MYSQL_DATABASE_NAME = os.environ['MYSQL_DATABASE_NAME']

mydb = mysql.connector.connect(
    host="localhost",
    user=MYSQL_USERNAME,
    password=MYSQL_PASSWORD,
    database=MYSQL_DATABASE_NAME
)
cursor = mydb.cursor()
cursor.execute(
    '''
    CREATE TABLE IF NOT EXISTS standup_data (
        DATE varchar(25),
        TIME varchar(25),
        USERID varchar(25),
        USERNAME varchar(25),
        Y_UPDATE varchar(250),
        T_UPDATE varchar(250),
        BLOCKER varchar(250)
        )
    '''
)

app = App(token=SLACK_BOT_TOKEN)


logger = logging.getLogger(__name__)


def log_request(logger, body, next):
    logger.debug(body)
    next()

# Reminder Message
def sendmessage():
    tomorrow = datetime.date.today()
    scheduled_time = datetime.time(hour=17, minute=29)
    schedule_timestamp = datetime.datetime.combine(
        tomorrow, scheduled_time).timestamp()
    try:
        app.client.chat_scheduleMessage(
            channel="C05RPRZD80K",
            post_at=schedule_timestamp,
            text="Kindly submit your standups"
        )
        print("schedule for today")
    except:
        print("schedule for tomorrow")
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)

sendmessage()


@app.event("message")
def handle_message_events(body, logger):
    logger.info(body)
    

def store_standup_data(standup_data):
    DATE = standup_data[0]
    TIME = standup_data[1]
    USERID = standup_data[2]
    USERNAME = standup_data[3]
    Y_UPDATE = standup_data[4]
    T_UPDATE = standup_data[5]
    BLOCKER = standup_data[6]

    sql = "INSERT INTO standup_data (DATE, TIME, USERID, USERNAME, Y_UPDATE, T_UPDATE, BLOCKER) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    val = (DATE, TIME, USERID, USERNAME, Y_UPDATE, T_UPDATE, BLOCKER)
    cursor.execute(sql, val)
    mydb.commit()


# Check for the Late Standup calls
def check_for_time(time):
    print(time)
    start_time = time.replace(hour=15, minute=30, second=0, microsecond=0)
    end_time = time.replace(hour=17, minute=45, second=0, microsecond=0)

    if time < start_time:
        return "0"
    elif time < end_time:
        return True
    else:
        return "1"


@app.command("/standup")
def create_standup(ack, body, logger, client):

    time = datetime.datetime.now()
    permit = check_for_time(time)

    if permit == True:
        ack()
        try:
            response = client.views_open(
                trigger_id=body["trigger_id"],
                view={

                    "type": "modal",
                    "title": {
                            "type": "plain_text",
                            "text": "Standup Bot"
                    },
                    "submit": {
                        "type": "plain_text",
                        "text": "Submit Standup",
                        "emoji": True
                    },
                    "close": {
                        "type": "plain_text",
                        "text": "Cancel",
                        "emoji": True
                    },
                    "callback_id": "submit_your_standup",
                    "clear_on_close": True,
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                    "type": "plain_text",
                                    "text": "Kindly update your standup.",
                                    "emoji": True
                            }
                        },
                        {
                            "type": "divider"
                        },
                        {
                            "type": "input",
                            "element": {
                                    "type": "plain_text_input",
                                    "multiline": True,
                                    "action_id": "plain_text_input-action-y"
                            },
                            "label": {
                                "type": "plain_text",
                                "text": "What you did yesterday?",
                                "emoji": True
                            }
                        },
                        {
                            "type": "input",
                            "element": {
                                    "type": "plain_text_input",
                                    "multiline": True,
                                    "action_id": "plain_text_input-action-t"
                            },
                            "label": {
                                "type": "plain_text",
                                "text": "What will you do today?",
                                "emoji": True
                            }
                        },
                        {
                            "type": "input",
                            "element": {
                                    "type": "plain_text_input",
                                    "action_id": "plain_text_input-action-b"
                            },
                            "label": {
                                "type": "plain_text",
                                "text": "What are the Blockers",
                                "emoji": True
                            }
                        }
                    ]

                }
            )

            logger.info(response)

        except SlackApiError as e:
            logger.error("Error creating conversation: {}".format(e))

    elif permit == "0":
        ack()
        response = client.views_open(
            trigger_id=body["trigger_id"],
            view={

                "type": "modal",
                "title": {
                    "type": "plain_text",
                    "text": "Access Denied"
                },
                "close": {
                    "type": "plain_text",
                    "text": "Ok",
                    "emoji": True
                },
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                                "type": "plain_text",
                                "text": "Standup is not opened yet.",
                                "emoji": True
                        }
                    }
                ]

            }
        )

        logger.info(response)

    elif permit == "1":
        ack()
        response = client.views_open(
            trigger_id=body["trigger_id"],
            view={

                "type": "modal",
                "title": {
                    "type": "plain_text",
                    "text": "Access Denied"
                },
                "close": {
                    "type": "plain_text",
                    "text": "Ok",
                    "emoji": True
                },
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                                "type": "plain_text",
                                "text": "Standup timed out.",
                                "emoji": True
                        }
                    }
                ]

            }
        )

        logger.info(response)

    else:
        ack()
        response = client.views_open(
            trigger_id=body["trigger_id"],
            view={

                "type": "modal",
                "title": {
                    "type": "plain_text",
                    "text": "Error"
                },
                "close": {
                    "type": "plain_text",
                    "text": "Ok",
                    "emoji": True
                },
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                                "type": "plain_text",
                                "text": "There is some error in updating your standup. Pls contact your admin.",
                                "emoji": True
                        }
                    }
                ]

            }
        )

        logger.info(response)


@app.view('submit_your_standup')
def submit_standup(body, ack):
    ack()
    standup_data = []

    # Username and UserID
    user_id = body['user']['id']
    user_name = body['user']['username']
    # Stanup Data
    standup_dataset = body['view']['state']['values']
    # Standup Date
    standup_date = str(datetime.date.today())
    # Standup Time
    now = datetime.datetime.now()
    standup_time = now.strftime("%H:%M:%S")

    standup_data.append(standup_date)
    standup_data.append(standup_time)
    standup_data.append(user_id)
    standup_data.append(user_name)

    for data in standup_dataset:
        for data_id in standup_dataset[data]:
            standup_data.append(standup_dataset[data][data_id]['value'])

    print(standup_data)

    store_standup_data(standup_data)
    data = {
        "user_id": user_id,
        "standup_data": {
            "date": standup_date,
            "time": standup_time,
            "user_name": user_name,
            "y_update": standup_data[4],
            "t_update": standup_data[5],
            "blocker": standup_data[6]
        }
    }
    dynamodb.store_data(data)
    app.client.chat_postMessage(
        channel="C05RPRZD80K",
        text="Standup added successfully"
    )


admins = ['U05NE6QN32A']


@app.command("/getfile")
def generate_file(ack, body, logger, client):
    todays_date = datetime.date.today()
    ack()
    response = client.views_open(
        trigger_id=body["trigger_id"],
        view={

            "type": "modal",
            "title": {
                    "type": "plain_text",
                    "text": "Generate Standup File"
            },
            "submit": {
                "type": "plain_text",
                "text": "Generate File",
                "emoji": True
            },
            "close": {
                "type": "plain_text",
                "text": "Cancel",
                "emoji": True
            },
            "callback_id": "generate_file",
            "clear_on_close": True,
            "blocks": [
                {
                    "type": "input",
                    "optional": True,
                    "element": {
                            "type": "multi_conversations_select",
                        "placeholder": {
                                    "type": "plain_text",
                            "text": "Select users",
                            "emoji": True
                        },
                        "filter": {
                            "include": [
                                "im"
                            ],
                            "exclude_bot_users": True
                        },
                        "action_id": "multi_users_select-action"
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Input type Select users",
                        "emoji": True
                    }
                },
                {
                    "type": "input",
                    "optional": True,
                    "element": {
                            "type": "checkboxes",
                        "options": [
                                    {
                                        "text": {
                                            "type": "plain_text",
                                            "text": "Select all Users",
                                            "emoji": True
                                        },
                                        "value": "value-0"
                                    }
                        ],
                        "action_id": "checkboxes-action"
                    },
                    "label": {
                        "type": "plain_text",
                        "text": " ",
                        "emoji": True
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "input",
                    "element": {
                            "type": "datepicker",
                        "initial_date": "2023-09-12",
                        "placeholder": {
                                    "type": "plain_text",
                                        "text": "Select a date",
                                        "emoji": True
                        },
                        "action_id": "datepicker-action"
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "From",
                        "emoji": True
                    }
                },
                {
                    "type": "input",
                    "element": {
                            "type": "datepicker",
                        "initial_date": f"{todays_date}",
                        "placeholder": {
                                    "type": "plain_text",
                                        "text": "Select a date",
                                        "emoji": True
                        },
                        "action_id": "datepicker-action"
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "To",
                        "emoji": True
                    }
                }
            ]

        }
    )

    logger.info(response)


if __name__ == "__main__":
    SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN")).start()
