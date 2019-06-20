# campusbot

![Overall System Design](overall-system-design.png)

The CampusBot API repository: [https://github.com/enreina/campusbot-api](https://github.com/enreina/campusbot-api)

We use Google Firestore for our database. Exhaustive schema descriptions for each collection can be seen here: [CampusBot Database Structure](https://docs.google.com/document/d/13jITw5RtkcE60GvN-HtvoUBkVkW_MdHu_eqWAu7p5w4/edit?usp=sharing).

## Setting up telegram bot

## How to Run (for development environment)
1. Setup a python virtual environment
2. Install the requirements `pip install -r requirements.txt`
3. Create an `.env` file (see `.env.sample`)
4. Add execute permission to `chmod +x campusbot-start`
5. Run the chatbot `./start campusbot-start`

## How to Deploy (for production environment)
