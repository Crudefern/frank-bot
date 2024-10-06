from cogs.abstractors.db_abstractor import mySQL

myDB = mySQL()

print(myDB.get_donor_json_ready_for_transfer()[0])
