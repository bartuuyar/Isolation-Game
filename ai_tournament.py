import time
from game import Game, PLAYER1, PLAYER2
from gui import GUI
import json
from datetime import datetime
import os
import csv
import pandas as pd

class AITournament:
    def __init__(self):
        self.results_dir = "tournament_results"
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
        self.checkpoint_dir = os.path.join(self.results_dir, "checkpoints")
        if not os.path.exists(self.checkpoint_dir):
            os.makedirs(self.checkpoint_dir)
    
    def save_checkpoint(self, all_results, current_match, total_matches, timestamp):
        checkpoint = {
            "timestamp": timestamp,
            "current_match": current_match,
            "total_matches": total_matches,
            "matches": all_results["matches"]
        }
        checkpoint_file = os.path.join(self.checkpoint_dir, f"checkpoint_{timestamp}.json")
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        print(f"Checkpoint saved: {checkpoint_file}")
    
    def load_latest_checkpoint(self):
        if not os.path.exists(self.checkpoint_dir):
            print("No checkpoint directory found. Starting fresh tournament.")
            return None
        
        try:
            checkpoints = [f for f in os.listdir(self.checkpoint_dir) if f.startswith("checkpoint_")]
            if not checkpoints:
                print("No checkpoints found. Starting fresh tournament.")
                return None
            
            latest_checkpoint = max(checkpoints)
            checkpoint_file = os.path.join(self.checkpoint_dir, latest_checkpoint)
            
            with open(checkpoint_file, 'r') as f:
                checkpoint = json.load(f)
            
            print(f"Loaded checkpoint: {checkpoint_file}")
            print(f"Progress: {checkpoint['current_match']}/{checkpoint['total_matches']} matches completed")
            return checkpoint
        except Exception as e:
            print(f"Error loading checkpoint: {str(e)}")
            print("Starting fresh tournament.")
            return None

    def run_match(self, config1, config2, num_games=1):
        results = {
            "config1": config1,
            "config2": config2,
            "games": [],
            "summary": {
                "config1_wins": 0,
                "config2_wins": 0,
                "avg_moves": 0,
                "avg_duration_sec": 0,
                "config1_depth": config1["depth"],
                "config2_depth": config2["depth"],
                "config1_position": config1.get("start_pos", "default"),
                "config2_position": config2.get("start_pos", "default")
            }
        }

        total_moves = 0
        total_duration = 0

        for game_num in range(num_games):
            game = Game(mode='AI vs AI', first_player=1)

            if 'start_pos' in config1:
                x, y = config1['start_pos']
                game.board[y][x] = PLAYER1
            if 'start_pos' in config2:
                x, y = config2['start_pos']
                game.board[y][x] = PLAYER2

            moves = 0
            game_record = {
                "moves": [],
                "winner": None,
                "move_count": 0,
                "duration_sec": 0,
                "blackout_positions": []
            }

            start_time = time.time()

            while not game.is_terminal():
                current_player = game.current_player
                config = config1 if current_player == PLAYER1 else config2

                action = game.best_action_for(current_player, config['depth'])
                if action:
                    move, blacks = action
                    game.apply_move(move, current_player)
                    if blacks:
                        game.apply_blackouts(blacks)
                        game_record["blackout_positions"].extend(blacks)

                    game_record["moves"].append({
                        "player": "config1" if current_player == PLAYER1 else "config2",
                        "move": move,
                        "blackouts": blacks
                    })

                game.current_player = PLAYER1 if current_player == PLAYER2 else PLAYER2
                moves += 1

                if moves > 100:
                    game_record["winner"] = "draw"
                    break

            end_time = time.time()
            duration = end_time - start_time
            game_record["duration_sec"] = duration
            total_duration += duration

            if game_record["winner"] != "draw":
                winner = "config1" if game.current_player == PLAYER2 else "config2"
                game_record["winner"] = winner
                results["summary"][f"{winner}_wins"] += 1

            game_record["move_count"] = moves
            total_moves += moves
            results["games"].append(game_record)

        results["summary"]["avg_moves"] = total_moves / num_games
        results["summary"]["avg_duration_sec"] = total_duration / num_games

        return results


    def save_tournament_results(self, all_results, timestamp):
        # Save detailed JSON results
        json_filename = f"{self.results_dir}/tournament_{timestamp}.json"
        with open(json_filename, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        # Create summary DataFrame
        summary_data = []
        for match in all_results["matches"]:
            config1 = match["config1"]
            config2 = match["config2"]
            summary = match["results"]["summary"]
            
            summary_data.append({
                "config1_name": config1["name"],
                "config1_depth": config1["depth"],
                "config1_position": str(config1.get("start_pos", "default")),
                "config2_name": config2["name"],
                "config2_depth": config2["depth"],
                "config2_position": str(config2.get("start_pos", "default")),
                "config1_wins": summary["config1_wins"],
                "config2_wins": summary["config2_wins"],                
                "avg_moves": summary["avg_moves"],
                "avg_duration_sec": summary["avg_duration_sec"]
            })
        
        # Save CSV summary
        df = pd.DataFrame(summary_data)
        csv_filename = f"{self.results_dir}/tournament_summary_{timestamp}.csv"
        df.to_csv(csv_filename, index=False)
        
        print(f"\nResults saved:")
        print(f"- Detailed results: {json_filename}")
        print(f"- Summary CSV: {csv_filename}")
        
        return df

def main():
    tournament = AITournament()
    
    # Define symmetrical position pairs (mirrored positions)
    symmetrical_positions = [
           
        [(3, 3), (4, 4)],   
        [(4, 3), (3, 4)], 
        [(2, 2), (5, 5)],   
        [(1, 1), (6, 6)],   
        [(2, 0), (5, 7)],   
        [(3, 0), (4, 7)]
    ]
    
    
    all_positions = [pos for pair in symmetrical_positions for pos in pair]
    
    # Generate AI configurations
    depths = range(1, 5)  # Depths 1-4
    configs = []
    for depth in depths:
        for pos in all_positions:
            cfg = {
                "name": f"depth{depth}_pos{pos[0]}{pos[1]}",
                "depth": depth,
                "start_pos": pos
            }
            configs.append(cfg)
    
    print("Generated configurations:")
    for cfg in configs:
        print(f"- {cfg['name']}")

    # Build match pairs
    match_pairs = []
    for i in range(len(configs)):
        for j in range(i + 1, len(configs)):
            pos_i = configs[i]["start_pos"]
            pos_j = configs[j]["start_pos"]
            
            #skip if positions are identical 
            if pos_i == pos_j:
                continue
            
            
            is_symmetrical = any(
                {pos_i, pos_j} == set(pair)  
                for pair in symmetrical_positions
            )
            
            if is_symmetrical:
                match_pairs.append((configs[i], configs[j]))
    
    total_matches = len(match_pairs)
    print(f"\nTotal symmetrical matches to be played: {total_matches}")

    
    checkpoint = tournament.load_latest_checkpoint()
    if checkpoint:
        if input("Found previous checkpoint. Resume? (y/n): ").lower() == "y":
            all_results = {
                "timestamp": checkpoint["timestamp"],
                "matches": checkpoint["matches"]
            }
            start_match = len(checkpoint["matches"])
        else:
            checkpoint = None
    
    if not checkpoint:
        if input("Run all matches from scratch? (y/n): ").lower() != "y":
            print("Exiting.")
            return
        
        all_results = {
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "matches": []
        }
        start_match = 0
    
    try:
        for match_num, (config1, config2) in enumerate(match_pairs[start_match:], start=start_match + 1):
            print(f"\nMatch {match_num}/{total_matches}: {config1['name']} vs {config2['name']}")
            results = tournament.run_match(config1, config2, num_games=1)
            print(f"Results: {results['summary']}")
            
            all_results["matches"].append({
                "config1": config1,
                "config2": config2,
                "results": results
            })
            
            tournament.save_checkpoint(all_results, match_num, total_matches, all_results["timestamp"])
        
        tournament.save_tournament_results(all_results, all_results["timestamp"])
        print("\nTournament completed successfully!")
    
    except Exception as e:
        print(f"\nError occurred: {e}")
        print("Progress saved. Resume from the last checkpoint.")
        raise

if __name__ == "__main__":
    main() 