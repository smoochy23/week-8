#!/usr/bin/env python3
import http.client
import json
from pandas import DataFrame
from datetime import datetime as dt
import click as cli

BASE_URL_DOMAIN = "disease.sh"
API_VERSION = "/v3/covid-19"

def get_remote_data(path, query_params=None):
    """Retrieve information from a web source."""
    connection = http.client.HTTPSConnection(BASE_URL_DOMAIN)
    headers = {'Content-type': 'application/json'}
    full_path = f"{API_VERSION}/{path}"
    if query_params:
        encoded_params = '&'.join([f"{key}={value}" for key, value in query_params.items()])
        full_path += f"?{encoded_params}"
    connection.request("GET", full_path, headers=headers)
    response = connection.getresponse()
    if response.status == 200:
        data = response.read().decode('utf-8')
        return json.loads(data)
    else:
        cli.echo(f"Encountered an issue fetching data: {response.status} {response.reason}")
        return None

    connection.close()

@cli.group()
def tracker_cli():
    """A tool for observing global and specific-nation COVID-19 figures."""
    pass

@tracker_cli.command()
def overall():
    """Show the latest global COVID-19 situation."""
    relevant_info = get_remote_data("all")
    if relevant_info:
        cli.echo(cli.style("--- Global COVID-19 Overview ---", fg="cyan", bold=True))
        cli.echo(f"Total Infections: {cli.style(f'{relevant_info['cases']:,}', fg='yellow')}")
        cli.echo(f"Total Fatalities: {cli.style(f'{relevant_info['deaths']:,}', fg='red')}")
        cli.echo(f"Total Recoveries: {cli.style(f'{relevant_info['recovered']:,}', fg='green')}")
        cli.echo(f"Currently Infected: {cli.style(f'{relevant_info['active']:,}', fg='magenta')}")
        cli.echo(f"New Infections Today: {cli.style(f'{relevant_info['todayCases']:,}', fg='yellow')}")
        cli.echo(f"New Fatalities Today: {cli.style(f'{relevant_info['todayDeaths']:,}', fg='red')}")
        timestamp = relevant_info['updated'] / 1000
        readable_time = dt.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        cli.echo(f"Last Refreshed: {readable_time}")

@tracker_cli.command()
@cli.argument('nation')
def nation_stats(nation):
    """Get the most recent COVID-19 statistics for a given NATION."""
    nation_data = get_remote_data(f"countries/{nation}")
    if nation_data:
        cli.echo(cli.style(f"--- COVID-19 Stats for {nation_data['country']} ---", fg="cyan", bold=True))
        cli.echo(f"Infections: {cli.style(f'{nation_data['cases']:,}', fg='yellow')}")
        cli.echo(f"Deaths: {cli.style(f'{nation_data['deaths']:,}', fg='red')}")
        cli.echo(f"Recovered: {cli.style(f'{nation_data['recovered']:,}', fg='green')}")
        cli.echo(f"Active: {cli.style(f'{nation_data['active']:,}', fg='magenta')}")
        cli.echo(f"Today's Infections: {cli.style(f'{nation_data['todayCases']:,}', fg='yellow')}")
        cli.echo(f"Today's Deaths: {cli.style(f'{nation_data['todayDeaths']:,}', fg='red')}")
        cli.echo(f"Total Tests Conducted: {cli.style(f'{nation_data['tests']:,}', fg='blue')}")
        timestamp = nation_data['updated'] / 1000
        readable_time = dt.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        cli.echo(f"Updated On: {readable_time}")
    else:
        cli.echo(f"Could not locate information for: {nation}")

@tracker_cli.command()
@cli.argument('place')
@cli.option('--history', default=7, help='Number of past days of data to show.')
def past_data(place, history):
    """Show historical COVID-19 data for a specific PLACE."""
    parameters = {"lastdays": history, "full": True}
    history_info = get_remote_data(f"historical/{place}", parameters)
    if history_info and 'timeline' in history_info:
        timeline = history_info['timeline']
        cases_frame = DataFrame(timeline['cases'].items(), columns=['Date', 'Infections'])
        deaths_frame = DataFrame(timeline['deaths'].items(), columns=['Date', 'Fatalities'])
        recovered_frame = DataFrame(timeline['recovered'].items(), columns=['Date', 'Recoveries'])

        cases_frame['Date'] = DataFrame.to_datetime(cases_frame['Date'])
        deaths_frame['Date'] = DataFrame.to_datetime(deaths_frame['Date'])
        recovered_frame['Date'] = DataFrame.to_datetime(recovered_frame['Date'])

        cli.echo(cli.style(f"--- Past COVID-19 Data for {history_info['country']} (Last {history} Days) ---", fg="cyan", bold=True))
        cli.echo(cli.style("\n--- Infections Over Time ---", fg="yellow", bold=True))
        cli.echo(cases_frame.to_string(index=False))
        cli.echo(cli.style("\n--- Fatalities Over Time ---", fg="red", bold=True))
        cli.echo(deaths_frame.to_string(index=False))
        cli.echo(cli.style("\n--- Recoveries Over Time ---", fg="green", bold=True))
        cli.echo(recovered_frame.to_string(index=False))
    else:
        cli.echo(f"Could not retrieve past data for {place} spanning {history} days.")

if __name__ == '__main__':
    tracker_cli()