from asociety.personality.cfa_utils import perform_cfa
import argparse

def main():
    parser = argparse.ArgumentParser(description='Perform Confirmatory Factor Analysis (CFA) on personality data.')
    parser.add_argument('--db-path', type=str, default='data/db/backup/deepseek-chat-narrative-old.db', help='Path to the SQLite database file.')
    
    args = parser.parse_args()
    
    results = perform_cfa(args.db_path)
    print(results)

if __name__ == '__main__':
    main()

