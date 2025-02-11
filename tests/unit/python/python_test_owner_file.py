import dolphin_project

# Create an instance of the Account class
bob = dolphin_project.Owner("Bob")
alice = dolphin_project.Owner("Alice")
account = dolphin_project.Account(lamports=100, data=[1, 2, 3], owner=alice)

# Print the account's representation
print(account)

# Get the account's length
print(len(account))

# Check the account's truthiness
print(bool(account))

# Try updating the account's data
account.update_data([4, 5, 6])
print(account)

# Set the account's lamports
account.lamports = 200

# Update the account's owner
account.set_owner(bob)  # Use set_owner instead of direct assignment
print(account)

# Compare this with another account
account2 = dolphin_project.Account(lamports=100, data=[1, 2, 3], owner=alice)
print(account2 == account)

# Get the Signer 
signer = dolphin_project.Signer()
print("Signer Key:", signer.key)  # ✅ Now accessible

# Get the Program Key and Sign
program = dolphin_project.Program()
print("Program Key:", program.key)  # ✅ Now accessible
print("Program Invoke:", program.invoke())


# Get the real time and Solana slot and epoch 
clock = dolphin_project.Clock()
print("Slot:", clock.slot())  
print("Epoch:", clock.epoch())  
print("Unix Timestamp:", clock.unix_timestamp()) 

