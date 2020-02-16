import datetime
import os
import requests
from time import sleep
import tweepy

class Committee:

    def __init__(self, id, name, treasurer_name, first_file_date):
        self.id = id
        self.name = name
        self.treasurer_name = treasurer_name
        self.first_file_date = first_file_date
        self.city = ""
        self.state = ""
        self.coh = 0.0



def retrieve_committee_data(FEC_API_KEY):
    response = requests.get(f"https://api.open.fec.gov/v1/committees?api_key={FEC_API_KEY}&sort_nulls_last=True&sort=-first_file_date")

    responseJson = response.json()

    # Retrieve committee IDs for the past day
    committee_list = []
    date_cutoff = datetime.date.today() - datetime.timedelta(days=2)
    for results in responseJson["results"]:
        formatted_file_date = datetime.datetime.strptime(results["first_file_date"], "%Y-%m-%d").date()
        if(formatted_file_date < date_cutoff):
            break
        committee_list.append(Committee(results["committee_id"], results["name"], results["treasurer_name"], results["first_file_date"]))

    # Retrieve individual data on committees
    for committee in committee_list:
        committee_data = requests.get(f"https://api.open.fec.gov/v1/committee/{committee.id}?api_key={FEC_API_KEY}").json()
        committee.city = committee_data["results"][0]["city"]
        committee.state = committee_data["results"][0]["state"]

        committee_filings = requests.get(f"https://api.open.fec.gov/v1/committee/{committee.id}/filings?api_key={FEC_API_KEY}&most_recent=True").json()
        if(len(committee_filings["results"]) > 0):
            committee.coh = committee_filings["results"][0]["cash_on_hand_end_period"] if committee_filings["results"][0]["cash_on_hand_end_period"] is not None else 0.0
        else:
            committee.coh = 0.0

    return committee_list


def main():
    FEC_API_KEY = os.environ.get("FEC_API_KEY")
    CONSUMER_KEY = os.environ.get("CONSUMER_KEY")
    CONSUMER_SECRET = os.environ.get("CONSUMER_SECRET")
    ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
    ACCESS_TOKEN_SECRET = os.environ.get("ACCESS_TOKEN.SECRET")

    # tweepy auth
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

    api = tweepy.API(auth)

    while(True):
        committee_list = retrieve_committee_data(FEC_API_KEY)
        for committee in committee_list:
            api.update_status(f"{committee.id}: {committee.name} was registered by {committee.treasurer_name} in {committee.city}, {committee.state}. First file date: {committee.first_file_date}, COH: ${committee.coh}")
        # sleep for 24 hours
        sleep(60 * 60 * 24)

if __name__ == "__main__":
    main()
