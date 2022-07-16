
from flask import Flask, request
import json
import os
import psycopg2
from twilio.twiml.messaging_response import MessagingResponse

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
# if not os.getenv("DATABASE_URL"):
#     raise RuntimeError("DATABASE_URL is not set")

# Set up database

engine = create_engine("postgresql+psycopg2://postgres:hoop@localhost/guided")

# engine = create_engine(os.getenv("postgresql+psycopg2://postgres:hoop@localhost/guided"))
db = scoped_session(sessionmaker(bind=engine))

country_codes = ['DZ','AO','BJ']

ls_dict = [{'code': 'q1', 'q': "Q1: What type of Loan are you currently having right now?\n\n-Property\n\n-Personal\n\n-Education\n\n-Medical\n\n-Auto\n\n-Business\n\n-None", 'answers': ['property', 'personal', 'education', 'medical', 'auto', 'business', 'none']},
{'code': 'q2', 'q': "Q2: From Scale 1 to 5 (5 being the highest), Will a well structured Loan improve you financial and social wellbeing right now?", 'answers': ['1', '2', '3', '4', '5']},
{'code': 'q3', 'q': "Q3: Are you currently using any BNPL at the moment? \n\n-Yes \n\n-No", 'answers': ['yes', 'no']},
{'code': 'q4', 'q': "Q4: What is the loan amount that you think ideally can help you reduce some of the financial commitment / burden right now? \n\n-A for MYR 1,000+ \n\n-B for MYR 5,000+ \n\n-C for MYR 10,000+ \n\n-D for MYR 20,000+", 'answers' : ['a', 'b', 'c', 'd']},
{'code': 'q5', 'q': "Q5: And last question; Are you currently renting or owning the place that you are staying right now? \n\n-Rent \n\n-Own", 'answers': ['rent', 'own']}
]


questions = ['q1', 'q2', 'q3', 'q4', 'q5']


@app.route('/bot', methods=['POST'])



def bot():
    incoming_msg = request.values.get('Body', '').lower()
    resp = MessagingResponse()
    msg = resp.message()
    responded = False
    incoming_num = request.values.get('From', '')
    number = incoming_num.strip('whatsapp:')
    
    #is there a better way to access the column values without having to go and check which row number it is???
    exists = db.execute("SELECT * from users WHERE phone = :phone", {'phone': number}).fetchall()
    if exists:
        username = exists[0][2]
        current_country = exists[0][1]
        print(current_country)
        # user_id = exists[0][0]
        score = exists[0][3]

        if username is None:
            db.execute("UPDATE users SET name = :name WHERE phone = :number", {'name': incoming_msg, 'number': number})
            db.commit()
            msg.body(f'Thank you {incoming_msg}! To start your survey, send "begin"\n\nWhen you want to leave the survey, please send "exit survey".\n\nRemember: spelling, accents, and hyphens count! Good luck!')
            responded = True

        elif 'menu' in incoming_msg:
            msg.body(f'Send "begin" to start survey and "exit survey" to quit the survey.')

            responded = True
        
        elif 'begin' in incoming_msg:

            db.execute("UPDATE users SET score = :score WHERE phone = :phone", {'score': 0, 'phone': number})
            db.commit()
            country = random_country(number)
            msg.body(f"{country}")

            responded = True

        elif 'exit survey' in incoming_msg:
            db.execute("UPDATE users SET score = 0, current_country = NULL WHERE phone = :number", {'number': number})
            db.commit()
            msg.body(f"Thanks for playing! You have answered {score} question(s). \n\nSend 'begin' when you want to reset your answers again!\n\nOr, visit this link for more information on Ello Technology: www.ellotechnology.com")
            responded = True
        
        elif current_country is not None:
            exists = db.execute("SELECT * from users WHERE phone = :phone", {'phone': number}).fetchall()
            indexn = int(exists[0][3])
            country = random_country(number)
            
            capital = ls_dict[indexn]['answers']
            if incoming_msg in capital:
                increase_score(number, score)
                exists = db.execute("SELECT * from users WHERE phone = :phone", {'phone': number}).fetchall()
                score = int(exists[0][3])
                
                if score == 5:
                    msg.body("Thanks for completing the survey! \n\nSend 'begin' when you want to reset your survey answers!\n\nOr, visit this link to gain more insights on our latest offering: https://wwww.ellotechnology.com")
                    
                else:
                    country = random_country(number)
                    msg.body(f"\n\n{country}")
            else:
                
                msg.body(f"Incorrect! Please answer from the options. To quit send 'exit survey'.\n\n{country}")
            responded = True
    
    if not exists:
        db.execute("INSERT INTO users (phone) VALUES (:phone)", {'phone': number})
        db.commit()
        msg.body("Hello! Welcome to the Ello Survey! What's your name?")
        responded = True

    if not responded:
        msg.body('I only know about things in the menu, sorry! Enter "menu" for the guide.')
    return str(resp)



def random_country(number):
    exists = db.execute("SELECT * from users WHERE phone = :phone", {'phone': number}).fetchall()
    # country_code = random.choice(country_codes)
    indexn = int(exists[0][3])
    country_code = questions[indexn]
    db.execute("UPDATE users SET current_country = :country WHERE phone = :number", {'country': country_code, 'number': number})
    db.commit()

    #search dictionary by code for q (country_code)
    country = ls_dict[indexn]['q']



    # country = info['name']
    return country
    # print(info)



def increase_score(number, score):
    score = score + 1
    db.execute("UPDATE users SET score = :score WHERE phone = :number", {'score': score, 'number': number})
    db.commit()



# questions



if __name__ == '__main__':
    app.run()
