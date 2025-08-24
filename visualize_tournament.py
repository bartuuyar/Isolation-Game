import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

class TournamentVisualizer:
    def __init__(self, results_dir="tournament_results"):
        self.results_dir = results_dir
        self.data = None
        self.summary_data = None
        
    def load_latest_tournament(self):
        """Load the most recent tournament results"""
        tournament_files = [f for f in os.listdir(self.results_dir) 
                            if f.startswith("tournament_") and f.endswith(".json")]
        if not tournament_files:
            raise FileNotFoundError("No tournament results found")
        
        latest_file = max(tournament_files)
        file_path = os.path.join(self.results_dir, latest_file)
        
        with open(file_path, 'r') as f:
            self.data = json.load(f)
            
        self.summary_data = pd.DataFrame([
            {
                "config1_name": match["config1"]["name"],
                "config1_depth": match["config1"]["depth"],
                "config1_position": str(match["config1"].get("start_pos", "default")),
                "config2_name": match["config2"]["name"],
                "config2_depth": match["config2"]["depth"],
                "config2_position": str(match["config2"].get("start_pos", "default")),
                "config1_wins": match["results"]["summary"]["config1_wins"],
                "config2_wins": match["results"]["summary"]["config2_wins"],
                "avg_moves": match["results"]["summary"]["avg_moves"],
                "avg_duration_sec": match["results"]["summary"]["avg_duration_sec"]
            }
            for match in self.data["matches"]
        ])
        
        print(f"Loaded tournament data from {latest_file}")
        return self.data
    
    def plot_win_rates_by_depth(self):
        """Plot win rates for different search depths"""
        if self.summary_data is None:
            raise ValueError("No tournament data loaded")
        
        depth_stats = []
        for depth in range(1, 5):  # depths used in tournament
            depth_matches = self.summary_data[
                (self.summary_data["config1_depth"] == depth) | 
                (self.summary_data["config2_depth"] == depth)
            ]
            wins_as_config1 = depth_matches[depth_matches["config1_depth"] == depth]["config1_wins"].sum()
            wins_as_config2 = depth_matches[depth_matches["config2_depth"] == depth]["config2_wins"].sum()
            total_matches = len(depth_matches)
            if total_matches == 0:
                continue
            win_rate = (wins_as_config1 + wins_as_config2) / total_matches
            depth_stats.append({
                "depth": depth,
                "win_rate": win_rate,
                "total_matches": total_matches
            })

        df = pd.DataFrame(depth_stats)
        plt.figure(figsize=(10, 6))
        sns.barplot(data=df, x="depth", y="win_rate")
        plt.title("Win Rate by Search Depth")
        plt.xlabel("Search Depth")
        plt.ylabel("Win Rate")
        plt.ylim(0, 1)

        for i, row in df.iterrows():
            plt.text(i, row["win_rate"] + 0.02, f"n={row['total_matches']}", ha='center')

        plt.savefig(os.path.join(self.results_dir, "win_rates_by_depth.png"))
        plt.close()
    
    def plot_win_rates_by_position(self):
        """Plot win rates for different starting positions"""
        if self.summary_data is None:
            raise ValueError("No tournament data loaded")
        
        position_stats = []
        positions = self.summary_data["config1_position"].unique()
        
        for pos in positions:
            pos_matches = self.summary_data[
                (self.summary_data["config1_position"] == pos) | 
                (self.summary_data["config2_position"] == pos)
            ]
            wins_as_config1 = pos_matches[pos_matches["config1_position"] == pos]["config1_wins"].sum()
            wins_as_config2 = pos_matches[pos_matches["config2_position"] == pos]["config2_wins"].sum()
            total_matches = len(pos_matches)
            if total_matches == 0:
                continue
            win_rate = (wins_as_config1 + wins_as_config2) / total_matches
            position_stats.append({
                "position": pos,
                "win_rate": win_rate,
                "total_matches": total_matches
            })

        df = pd.DataFrame(position_stats)
        plt.figure(figsize=(12, 6))
        sns.barplot(data=df, x="position", y="win_rate")
        plt.title("Win Rate by Starting Position")
        plt.xlabel("Starting Position")
        plt.ylabel("Win Rate")
        plt.ylim(0, 1)
        plt.xticks(rotation=45)

        for i, row in df.iterrows():
            plt.text(i, row["win_rate"] + 0.02, f"n={row['total_matches']}", ha='center')

        plt.tight_layout()
        plt.savefig(os.path.join(self.results_dir, "win_rates_by_position.png"))
        plt.close()
    
    def plot_avg_moves_by_depth(self):
        """Plot average number of moves by search depth"""
        if self.summary_data is None:
            raise ValueError("No tournament data loaded")
        
        depth_stats = []
        for depth in range(1, 5):
            depth_matches = self.summary_data[
                (self.summary_data["config1_depth"] == depth) | 
                (self.summary_data["config2_depth"] == depth)
            ]
            if len(depth_matches) == 0:
                continue
            avg_moves = depth_matches["avg_moves"].mean()
            depth_stats.append({
                "depth": depth,
                "avg_moves": avg_moves
            })

        df = pd.DataFrame(depth_stats)
        plt.figure(figsize=(10, 6))
        sns.barplot(data=df, x="depth", y="avg_moves")
        plt.title("Average Game Length by Search Depth")
        plt.xlabel("Search Depth")
        plt.ylabel("Average Number of Moves")

        plt.savefig(os.path.join(self.results_dir, "avg_moves_by_depth.png"))
        plt.close()
    
    def generate_summary_report(self):
        """Generate a comprehensive summary report"""
        if self.summary_data is None:
            raise ValueError("No tournament data loaded")

        report = []
        report.append("# Tournament Summary Report")
        report.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        report.append("## Overall Statistics")
        report.append(f"Total matches played: {len(self.summary_data)}")
        report.append(f"Average game length: {self.summary_data['avg_moves'].mean():.2f} moves")
        report.append(f"Average duration: {self.summary_data['avg_duration_sec'].mean():.2f} sec")
        report.append(f"Shortest game: {self.summary_data['avg_moves'].min():.2f} moves")
        report.append(f"Longest game: {self.summary_data['avg_moves'].max():.2f} moves\n")

        report.append("## Analysis by Search Depth")
        for depth in range(1, 5):
            depth_matches = self.summary_data[
                (self.summary_data["config1_depth"] == depth) | 
                (self.summary_data["config2_depth"] == depth)
            ]
            if len(depth_matches) == 0:
                continue
            wins_as_config1 = depth_matches[depth_matches["config1_depth"] == depth]["config1_wins"].sum()
            wins_as_config2 = depth_matches[depth_matches["config2_depth"] == depth]["config2_wins"].sum()
            total_matches = len(depth_matches)
            win_rate = (wins_as_config1 + wins_as_config2) / total_matches

            report.append(f"\n### Depth {depth}")
            report.append(f"Total matches: {total_matches}")
            report.append(f"Win rate: {win_rate:.2%}")
            report.append(f"Average game length: {depth_matches['avg_moves'].mean():.2f} moves")
            report.append(f"Average duration: {depth_matches['avg_duration_sec'].mean():.2f} sec")

        report.append("\n## Analysis by Starting Position")
        positions = self.summary_data["config1_position"].unique()
        for pos in positions:
            pos_matches = self.summary_data[
                (self.summary_data["config1_position"] == pos) | 
                (self.summary_data["config2_position"] == pos)
            ]
            if len(pos_matches) == 0:
                continue
            wins_as_config1 = pos_matches[pos_matches["config1_position"] == pos]["config1_wins"].sum()
            wins_as_config2 = pos_matches[pos_matches["config2_position"] == pos]["config2_wins"].sum()
            total_matches = len(pos_matches)
            win_rate = (wins_as_config1 + wins_as_config2) / total_matches

            report.append(f"\n### Position {pos}")
            report.append(f"Total matches: {total_matches}")
            report.append(f"Win rate: {win_rate:.2%}")
            report.append(f"Average game length: {pos_matches['avg_moves'].mean():.2f} moves")
            report.append(f"Average duration: {pos_matches['avg_duration_sec'].mean():.2f} sec")

        report_path = os.path.join(self.results_dir, "tournament_summary.md")
        with open(report_path, 'w') as f:
            f.write('\n'.join(report))
        
        print(f"Summary report saved to: {report_path}")

def main():
    visualizer = TournamentVisualizer()
    
    try:
        visualizer.load_latest_tournament()
        print("Generating visualizations...")
        visualizer.plot_win_rates_by_depth()
        visualizer.plot_win_rates_by_position()
        visualizer.plot_avg_moves_by_depth()
        print("Generating summary report...")
        visualizer.generate_summary_report()
        print("\nAll visualizations and reports have been generated.")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
