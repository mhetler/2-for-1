import pandas as pd
import matplotlib.pyplot as plt
import os

# === Helper Functions ===

def clock_to_seconds(clock_str):
    if pd.isna(clock_str):
        return None
    clock_str = clock_str.replace('PT', '').replace('S', '')
    if 'M' in clock_str:
        minutes, seconds = clock_str.split('M')
        return int(minutes) * 60 + float(seconds)
    else:
        return float(clock_str)

def get_points(play_type, play_subtype, result, desc):
    if play_type not in ['Made Shot', 'Free Throw']:
        return 0
    if pd.isna(result):
        return 0
    if ('Three Point' in str(play_subtype)) or ('3PT' in str(desc)) or ('3 Point' in str(play_subtype)):
        return 3
    if play_type == 'Free Throw':
        return 1
    return 2

# === Era Bins ===

era1 = []  # 1997-2006
era2 = []  # 2007-2015
era3 = []  # 2016-2023

# === Folder where all your CSVs are ===

data_folder = "."# (your folder name)

# === Seasons to analyze ===

seasons = list(range(1997, 2024))  # 1997-2023

# === Start Era Processing ===

for year in seasons:
    season_file = f"{data_folder}/pbp{year}.csv"  # <<< CORRECT filename pattern
    season_label = f"{year-1}-{str(year)[-2:]}" if year < 2000 else f"{year}-{str(year+1)[-2:]}"
    
    if not os.path.exists(season_file):
        print(f"Missing {season_file}, skipping...")
        continue

    print(f"\nProcessing {season_label} season...")

    # Load season data
    df = pd.read_csv(season_file)
    df['SECONDS_LEFT'] = df['clock'].apply(clock_to_seconds)

    # Focus on last 40 seconds and valid shot events
    df = df[df['type'].isin(['Made Shot', 'Missed Shot', 'Free Throw'])]
    df = df[df['SECONDS_LEFT'] <= 40]
    df = df.dropna(subset=['team'])  # drop rows with missing team

    # Detect 2-for-1 sequences
    two_for_one_sequences = []

    grouped = df.groupby('gameid')

    for game_id, game_df in grouped:
        game_df = game_df.sort_values(['period', 'SECONDS_LEFT'], ascending=[True, False]).reset_index(drop=True)

        for i in range(len(game_df)):
            first_shot = game_df.iloc[i]
            first_time = first_shot['SECONDS_LEFT']
            first_period = first_shot['period']

            if not (30 <= first_time <= 38):
                continue

            team_a = first_shot['team']

            intervening_shot = None
            second_shot = None
            omit_sequence = False
            in_between_events = []

            for j in range(i + 1, len(game_df)):
                event = game_df.iloc[j]
                shot_time = event['SECONDS_LEFT']
                shot_period = event['period']

                if shot_period != first_period:
                    break

                if pd.isna(event['team']):
                    continue  # skip bad rows

                current_team = event['team']

                in_between_events.append(event)

                if intervening_shot is not None and current_team == team_a and 0 <= shot_time <= 14:
                    second_shot = event
                    break

                if intervening_shot is None and current_team != team_a:
                    intervening_shot = event

            for event in in_between_events:
                if event['type'] in ['Turnover', 'Foul']:
                    omit_sequence = True
                    break
                if intervening_shot is None:
                    omit_sequence = True
                    break

            if not omit_sequence and intervening_shot is not None and second_shot is not None:
                two_for_one_sequences.append((first_shot, intervening_shot, second_shot))

    # Score sequences
    season_pm = []

    for first, mid, second in two_for_one_sequences:
        team_a = first['team']

        first_pts = get_points(first['type'], first['subtype'], first['result'], first['desc'])
        mid_pts = get_points(mid['type'], mid['subtype'], mid['result'], mid['desc'])
        second_pts = get_points(second['type'], second['subtype'], second['result'], second['desc'])

        total_a = first_pts + second_pts
        total_b = mid_pts
        plus_minus = total_a - total_b

        season_pm.append(plus_minus)

    # Assign to correct era
    if 1997 <= year <= 2006:
        era1.extend(season_pm)
    elif 2007 <= year <= 2015:
        era2.extend(season_pm)
    else:
        era3.extend(season_pm)

# === Plotting ===

def plot_histogram(data, title, filename):
    plt.figure(figsize=(8,6))
    plt.hist(data, bins=range(-5,6), edgecolor='black', align='left')
    plt.title(title)
    plt.xlabel('Net Point Differential')
    plt.ylabel('Frequency')
    plt.grid(True)
    plt.savefig(filename)
    plt.show()

# === Summarize and Plot ===

print("\n=== Era 1: 1997–2006 ===")
print(f"Sequences: {len(era1)}")
print(f"Average +/-: {sum(era1)/len(era1):.2f}" if era1 else "No sequences.")
plot_histogram(era1, "2-for-1 Net Point Differential (1997–2006)", "era1_histogram.png")

print("\n=== Era 2: 2007–2015 ===")
print(f"Sequences: {len(era2)}")
print(f"Average +/-: {sum(era2)/len(era2):.2f}" if era2 else "No sequences.")
plot_histogram(era2, "2-for-1 Net Point Differential (2007–2015)", "era2_histogram.png")

print("\n=== Era 3: 2016–2023 ===")
print(f"Sequences: {len(era3)}")
print(f"Average +/-: {sum(era3)/len(era3):.2f}" if era3 else "No sequences.")
plot_histogram(era3, "2-for-1 Net Point Differential (2016–2023)", "era3_histogram.png")
