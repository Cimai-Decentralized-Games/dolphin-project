"""
Example demonstrating how to use the Dolphin Language (.dl) syntax
"""
from dolphin.dl.parser import DLParser
from dolphin.compiler import compile_program
import os

# Example .dl content (normally this would be in a separate file)
EXAMPLE_DL = '''
program TokenVault {
    id: "Vault9999999999999999999999999999999999999"
    
    account VaultState {
        authority: pubkey
        token_mint: pubkey
        total_deposits: u64
    }
    
    account UserDeposit {
        owner: pubkey
        amount: u64
        last_deposit_time: i64
    }
    
    ix initialize(authority: pubkey, token_mint: pubkey) {
        require(@signer == authority, "Only authority can initialize")
        
        @vault.authority = authority
        @vault.token_mint = token_mint
        @vault.total_deposits = 0
    }
    
    ix deposit(amount: u64) {
        require(amount > 0, "Amount must be positive")
        require(@token_account.mint == @vault.token_mint, "Invalid token mint")
        
        @user_deposit.owner = @signer
        @user_deposit.amount += amount
        @user_deposit.last_deposit_time = @clock.unix_timestamp
        
        @vault.total_deposits += amount
    }
    
    ix withdraw(amount: u64) {
        require(amount > 0, "Amount must be positive")
        require(@user_deposit.owner == @signer, "Not the owner")
        require(@user_deposit.amount >= amount, "Insufficient balance")
        
        @user_deposit.amount -= amount
        @vault.total_deposits -= amount
    }
}
'''

def main():
    # 1. Save the DL content to a file
    dl_file = "token_vault.dl"
    with open(dl_file, "w") as f:
        f.write(EXAMPLE_DL)
    
    try:
        # 2. Parse the DL file
        print("Parsing Dolphin Language file...")
        with open(dl_file, "r") as f:
            content = f.read()
        
        parser = DLParser(content)
        program_ir = parser.parse()
        
        # 3. Print the parsed program structure
        print("\nParsed Program Structure:")
        print(f"Program Name: {program_ir.name}")
        print(f"Program ID: {program_ir.program_id}")
        
        print("\nAccounts:")
        for account in program_ir.accounts:
            print(f"  - {account.name}")
            for field in account.fields:
                print(f"    * {field.name}: {field.type_name}")
        
        print("\nInstructions:")
        for ix in program_ir.instructions:
            print(f"  - {ix.name}")
            for arg_name, arg_type in ix.args:
                print(f"    * {arg_name}: {arg_type}")
        
        # 4. Compile to Anchor program
        print("\nCompiling to Anchor program...")
        anchor_program = compile_program(program_ir)
        
        # 5. Save the generated Rust code
        output_dir = "target/programs/token_vault/src"
        os.makedirs(output_dir, exist_ok=True)
        
        with open(f"{output_dir}/lib.rs", "w") as f:
            f.write(anchor_program)
        
        print(f"\nGenerated Anchor program at: {output_dir}/lib.rs")
        
        # 6. Print next steps
        print("\nNext steps:")
        print("1. cd target/programs/token_vault")
        print("2. anchor build")
        print("3. anchor deploy")
        
    except SyntaxError as e:
        print(f"Syntax Error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up the temporary .dl file
        if os.path.exists(dl_file):
            os.remove(dl_file)

if __name__ == "__main__":
    main()