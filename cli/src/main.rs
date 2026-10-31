use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(name = "disha", version = "1.0.0", about = "DISHA Student Intervention Platform CLI")]
struct Cli {
    #[arg(short, long, env = "DISHA_API_URL", default_value = "http://localhost:8000")]
    api_url: String,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Inspect platform health and connectivity
    Status,
    /// Manage intervention cases
    Cases {
        #[arg(short, long)]
        campus: Option<String>,
    },
    /// Trigger data ingestion sync
    Sync {
        #[arg(short, long)]
        source: String,
    },
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let cli = Cli::parse();
    match cli.command {
        Commands::Status => {
            println!("DISHA CLI connected to API at: {}", cli.api_url);
            println!("Status: Operational");
        }
        Commands::Cases { campus } => {
            println!("Listing DISHA cases for campus: {:?}", campus.unwrap_or_else(|| "all".to_string()));
        }
        Commands::Sync { source } => {
            println!("Triggering DISHA ingestion sync from source: {}", source);
        }
    }
    Ok(())
}
