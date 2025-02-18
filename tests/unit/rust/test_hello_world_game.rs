use anchor_lang::prelude::*;
 
// This is your program's public key and it will update
// automatically when you build the project. This is key for Dolphin Development with Anchor
// This is what I need to do for Dolphin.  I need to create this but in python using Dolphin then test it 
// with the program. So my first users can really experiance the power of Dolphin!
declare_id!("BouPBVWkdVHbxsdzqeMwkjqd5X67RX5nwMEwxn8MDpor");
 
#[program]
mod tiny_adventure {
    use super::*;
 
    pub fn initialize(ctx: Context<Initialize>) -> Result<()> {
        ctx.accounts.new_game_data_account.player_position = 0;
        msg!("A Journey Begins!");
        msg!("o.......");
        Ok(())
    }
 
    pub fn move_left(ctx: Context<MoveLeft>) -> Result<()> {
        let game_data_account = &mut ctx.accounts.game_data_account;
        if game_data_account.player_position == 0 {
            msg!("You are back at the start.");
        } else {
            game_data_account.player_position -= 1;
            print_player(game_data_account.player_position);
        }
        Ok(())
    }
 
    pub fn move_right(ctx: Context<MoveRight>) -> Result<()> {
        let game_data_account = &mut ctx.accounts.game_data_account;
        if game_data_account.player_position == 3 {
            msg!("You have reached the end! Super!");
        } else {
            game_data_account.player_position = game_data_account.player_position + 1;
            print_player(game_data_account.player_position);
        }
        Ok(())
    }
}
 
fn print_player(player_position: u8) {
    if player_position == 0 {
        msg!("A Journey Begins!");
        msg!("o.......");
    } else if player_position == 1 {
        msg!("..o.....");
    } else if player_position == 2 {
        msg!("....o...");
    } else if player_position == 3 {
        msg!("........\\o/");
        msg!("You have reached the end! Super!");
    }
}
 
#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(
        init_if_needed,
        seeds = [b"level1"],
        bump,
        payer = signer,
        space = 8 + 1
    )]
    pub new_game_data_account: Account<'info, GameDataAccount>,
    #[account(mut)]
    pub signer: Signer<'info>,
    pub system_program: Program<'info, System>,
}
 
#[derive(Accounts)]
pub struct MoveLeft<'info> {
    #[account(mut)]
    pub game_data_account: Account<'info, GameDataAccount>,
}
 
#[derive(Accounts)]
pub struct MoveRight<'info> {
    #[account(mut)]
    pub game_data_account: Account<'info, GameDataAccount>,
}
 
#[account]
pub struct GameDataAccount {
    player_position: u8,
}

// In this development guide, we will walkthrough a simple on-chain game using the Solana blockchain. 
// This game, lovingly called Tiny Adventure, is a beginner-friendly Solana program created using the Anchor framework. 
// The goal of this program is to show you how to create a simple game
// that allows players to track their position and move left or right.

//In this example, a Program Derived Address (PDA) is used for the GameDataAccount address. This enables us to deterministically locate the address later on. It is important to note that the PDA in this example is generated with a single fixed value as the seed (level1), limiting our program to creating only one GameDataAccount. The init_if_needed constraint then ensures that the GameDataAccount is initialized only if it doesn't already exist.

// It is worth noting that the current implementation does not have any restrictions on who can modify the GameDataAccount. This effectively transforms the game into a multiplayer experience where everyone can control the player's movement.

// Alternatively, you can use the signer's address as an extra seed in the initialize instruction, which would enable each player to create their own GameDataAccount.

// Move Left Instruction
// Now that we can initialize a GameDataAccount account, let's implement the move_left instruction which allows a player update their player_position.

// In this example, moving left simply means decrementing the player_position by 1. We'll also set the minimum position to 0. The only account needed for this instruction is the GameDataAccount.
// Move Right Instruction
// Lastly, let's implement the move_right instruction. Similarly, moving right will simply mean incrementing the player_position by 1. We'll also limit the maximum position to 3.

// Just like before, the only account needed for this instruction is the GameDataAccount.