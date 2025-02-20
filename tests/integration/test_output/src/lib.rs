use anchor_lang::prelude::*;
use anchor_lang::solana_program::system_program;

declare_id!("Test666666666666666666666666666666666666666");

#[program]
pub mod testprogram {
    use super::*;

    #[account]
    #[derive(Default)]
    pub struct Counter {
        pub count: u64,
    }

    #[derive(Accounts)]
    pub struct increment {
    }

    pub fn increment(
        ctx: Context<Self>,
    ) -> Result<()> {
        counter.count = 1;
        Ok(())
    }


} // mod program
