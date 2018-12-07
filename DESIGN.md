# CrimsonCampaignCS50 - Design

Crimson Campaigns is a Flask app primarily focused on integration with and management
of SQL databases.

The dynamic generation of a database for every user did lead to some challenges,
such as the necessity of concatenating usernames into SQL command strings instead
of using the :variable syntax as database names cannot be encased in quotes.

In future revisions, I may change to use user IDs instead of usernames to protect
from SQL injection vulnerability, but I may instead just limit username inputs
and escape user characters to make management of all databases easier at a glance.

The key aspect of the implementation of this program is the tracking of the type of  
campaign a user has signed up for. This app is designed to be largely dynamic to
this fact, with both the frontend graphics and database structures changing to
match the needs of different forms of races, seeking to minimize redundancies.

Through both Pythonic and Jinja control, this variation comes into play in Navbar
graphics, form contents, the search form display, and database creation.

*I will admit that I struggled with time far more than I expected to, not sure
what part of that is over-ambition and which part comes to my own ability and
workflow.

Am feeling under the gun as the deadline is here and will work to finish what
I've started as much as possible and continue updating the git repository to have
the best possible product for the fair.

There's a lot to do for finishing features, polishing CSS, catching errors,
and preventing unwanted input. I probably should've had a partner.

As a result, this is currently fairly unfinished and not in the state I would have liked
it to be for presentation. However, I learned a lot and am still invested in
this idea, and would like to continue work on it, especially after learning more
through CS50 Beyond.

This idea was partially inspired by my work with the Harvard Votes Challenge,
and something like this could be useful for voter registration efforts come 2020*
