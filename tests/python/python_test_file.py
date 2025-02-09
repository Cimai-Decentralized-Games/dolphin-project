import dolphin_project

# Create an instance of the Account class
account = dolphin_project.Account(lamports=100, data=[1, 2, 3], owner="Alice")

# Print the account's representation
print(account)

# Get the account's length
print(len(account))

# Check the account's truthiness
print(bool(account))

# Try updating the account's data
account.update_data([4, 5, 6])
print(account)

# Set the account's lamports and owner
account.lamports = 200
account.owner = "Bob"
print(account)

# Compare this with another account
account2 = dolphin_project.Account(lamports=100, data=[1, 2, 3], owner="Alice")

print(account2 == account)