from cogs.abstractors.db_abstractor import the_db
from cogs.abstractors.cleaninty_abstractor import cleaninty_abstractor
cleaninty = cleaninty_abstractor()
myDB = the_db()

donors = myDB.read_donor_table()

for i in range(len(donors)):
    cleaninty.refresh_donor_lt_time(donors[i][0])
    print(donors[i][0])

myDB.exit()