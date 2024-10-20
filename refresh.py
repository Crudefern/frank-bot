from cogs.abstractors.db_abstractor import the_db
myDB = the_db()

donors = myDB.read_donor_table()

for i in range(len(donors)):
    myDB.refresh_donor_lt_time(donors[i][0])
    print(donors[i][0])

myDB.exit()