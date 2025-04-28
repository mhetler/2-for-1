import pandas as pd
import matplotlib.pyplot as plt
import os

# === Helper Functions ===
def time_to_seconds(time_str):
    try:
        minutes, seconds = map(int, time_str.replace('PT', '').replace('M', ':').replace('S', '').split(':'))
        return minutes * 60 + seconds
    except:
        return 0

def get_points(row):
    if row['type'] != 'Made Shot':
        return 0
    if '3PT' in (row['desc'] or ''):
        return 3
    if 'free throw' in (row['subtype'] or '').lower():
        return 1
    return 2

def process_season(file_path, season_year):
    df = pd.read_csv(file_path)
    df['SECONDS_LEFT'] = df['clock'].apply(time_to_seconds)
    df_final_40 = df[df['SECONDS_LEFT'] <= 40].copy()
    df_final_40 = df_final_40[df_final_40['type'].isin(['Made Shot', 'Missed Shot'])]

    season_plus_minus = []

    games = df_final_40['gameid'].unique()
    for game_id in games:
        df_game = df_final_40[df_final_40['gameid'] == game_id].reset_index(drop=True)
        for i in range(len(df_game)):
            first_shot = df_game.iloc[i]
            first_time = time_to_seconds(first_shot['clock'])
            first_period = first_shot['period']
            if not (30 <= first_time <= 38):
                continue

            team_a = first_shot['team']
            intervening_shot = None
            second_shot = None

            for j in range(i + 1, len(df_game)):
                event = df_game.iloc[j]
                shot_time = time_to_seconds(event['clock'])
                shot_period = event['period']
                if shot_period != first_period:
                    break

                if event['team'] != team_a and intervening_shot is None:
                    intervening_shot = event
                elif event['team'] == team_a and intervening_shot is not None and shot_time <= 14:
                    second_shot = event
                    break

            if intervening_shot is not None and second_shot is not None:
                first_pts = get_points(first_shot)
                mid_pts = get_points(intervening_shot)
                second_pts = get_points(second_shot)
                total_a = first_pts + second_pts
                total_b = mid_pts
                plus_minus = total_a - total_b
                season_plus_minus.append(plus_minus)

    return season_plus_minus

# === Main Processing ===

era1_pm = []
era2_pm = []
era3_pm = []
season_avg_pm = {}

for year in range(1997, 2024):
    filename = f'pbp{year}.csv'
    if not os.path.exists(filename):
        print(f"Missing {filename}, skipping...")
        continue

    print(f"Processing {year} season...")
    season_pm = process_season(filename, year)

    if 1997 <= year <= 2006:
        era1_pm.extend(season_pm)
    elif 2007 <= year <= 2015:
        era2_pm.extend(season_pm)
    else:
        era3_pm.extend(season_pm)

    if season_pm:
        season_avg_pm[year] = sum(season_pm) / len(season_pm)
    else:
        season_avg_pm[year] = 0

# === Combined Histogram ===
if not os.path.exists('output'):
    os.makedirs('output')

plt.figure(figsize=(10,6))
plt.hist(era1_pm, bins=range(-6,7), alpha=0.5, label='1997-2006')
plt.hist(era2_pm, bins=range(-6,7), alpha=0.5, label='2007-2015')
plt.hist(era3_pm, bins=range(-6,7), alpha=0.5, label='2016-2023')
plt.title('How 2-for-1 Strategy Efficiency Improved Over Time')
plt.xlabel('Net Point Differential')
plt.ylabel('Frequency')
plt.legend()
plt.grid(True)
plt.savefig('output/combined_histogram.png')
plt.show()

# === Trend Line of Average +/- ===
plt.figure(figsize=(10,6))
plt.plot(list(season_avg_pm.keys()), list(season_avg_pm.values()), marker='o')
plt.title('Average 2-for-1 Net Point Differential by Season')
plt.xlabel('Season')
plt.ylabel('Average Net Point Differential')
plt.grid(True)
plt.savefig('output/trendline_season_avg.png')
plt.show()

print("✅ Done! Combined graph and trendline saved in 'output/' folder!")
