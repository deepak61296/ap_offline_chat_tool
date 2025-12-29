#!/usr/bin/env python3
"""
Generate comprehensive comparison report from CSV results
"""

import csv
import json
import sys
from collections import defaultdict


def analyze_csv(csv_filename):
    """Analyze CSV and generate detailed comparison report"""
    
    # Read CSV
    results = []
    with open(csv_filename, 'r') as f:
        reader = csv.DictReader(f)
        results = list(reader)
    
    # Calculate statistics
    stats = {
        'qwen25': {'correct': 0, 'total': 0, 'times': [], 'by_function': defaultdict(lambda: {'correct': 0, 'total': 0})},
        'gemma3': {'correct': 0, 'total': 0, 'times': [], 'by_function': defaultdict(lambda: {'correct': 0, 'total': 0})},
        'ardupilot': {'correct': 0, 'total': 0, 'times': [], 'by_function': defaultdict(lambda: {'correct': 0, 'total': 0})}
    }
    
    for row in results:
        expected_func = row['Expected_Function']
        
        # Qwen 2.5
        if row['Qwen25_Correct'] == 'YES':
            stats['qwen25']['correct'] += 1
            stats['qwen25']['by_function'][expected_func]['correct'] += 1
        stats['qwen25']['total'] += 1
        stats['qwen25']['by_function'][expected_func]['total'] += 1
        stats['qwen25']['times'].append(float(row['Qwen25_Time']))
        
        # Gemma 3
        if row['Gemma3_Correct'] == 'YES':
            stats['gemma3']['correct'] += 1
            stats['gemma3']['by_function'][expected_func]['correct'] += 1
        stats['gemma3']['total'] += 1
        stats['gemma3']['by_function'][expected_func]['total'] += 1
        stats['gemma3']['times'].append(float(row['Gemma3_Time']))
        
        # ArduPilot
        if row['ArduPilot_Correct'] == 'YES':
            stats['ardupilot']['correct'] += 1
            stats['ardupilot']['by_function'][expected_func]['correct'] += 1
        stats['ardupilot']['total'] += 1
        stats['ardupilot']['by_function'][expected_func]['total'] += 1
        stats['ardupilot']['times'].append(float(row['ArduPilot_Time']))
    
    # Generate report
    print("="*100)
    print("COMPREHENSIVE MODEL COMPARISON REPORT")
    print("="*100)
    
    print(f"\nTotal Test Cases: {len(results)}")
    print(f"Test Categories: {len(set(r['Expected_Function'] for r in results))} different functions")
    
    # Overall Statistics
    print("\n" + "="*100)
    print("OVERALL PERFORMANCE")
    print("="*100)
    
    print(f"\n{'Model':<30} {'Accuracy':<15} {'Avg Time':<15} {'Min Time':<15} {'Max Time':<15}")
    print("-"*100)
    
    for model_name, model_key in [('Qwen 2.5 (3B)', 'qwen25'),
                                   ('Gemma 3 (4B)', 'gemma3'),
                                   ('ArduPilot Stage 1 (270M)', 'ardupilot')]:
        s = stats[model_key]
        accuracy = (s['correct'] / s['total'] * 100) if s['total'] > 0 else 0
        avg_time = sum(s['times']) / len(s['times']) if s['times'] else 0
        min_time = min(s['times']) if s['times'] else 0
        max_time = max(s['times']) if s['times'] else 0
        
        print(f"{model_name:<30} {accuracy:>6.1f}% ({s['correct']}/{s['total']})  {avg_time:>8.3f}s      {min_time:>8.3f}s      {max_time:>8.3f}s")
    
    # Per-Function Breakdown
    print("\n" + "="*100)
    print("PER-FUNCTION ACCURACY BREAKDOWN")
    print("="*100)
    
    functions = sorted(set(r['Expected_Function'] for r in results))
    
    for func in functions:
        print(f"\n{func.upper()}:")
        print(f"{'Model':<30} {'Accuracy':<20}")
        print("-"*50)
        
        for model_name, model_key in [('Qwen 2.5', 'qwen25'),
                                       ('Gemma 3', 'gemma3'),
                                       ('ArduPilot Stage 1', 'ardupilot')]:
            func_stats = stats[model_key]['by_function'][func]
            if func_stats['total'] > 0:
                accuracy = (func_stats['correct'] / func_stats['total'] * 100)
                print(f"{model_name:<30} {accuracy:>6.1f}% ({func_stats['correct']}/{func_stats['total']})")
    
    # Winner Analysis
    print("\n" + "="*100)
    print("WINNER ANALYSIS")
    print("="*100)
    
    # Best accuracy
    best_accuracy_model = max(stats.items(), key=lambda x: x[1]['correct'] / x[1]['total'] if x[1]['total'] > 0 else 0)
    best_accuracy = (best_accuracy_model[1]['correct'] / best_accuracy_model[1]['total'] * 100)
    
    # Fastest
    fastest_model = min(stats.items(), key=lambda x: sum(x[1]['times']) / len(x[1]['times']) if x[1]['times'] else float('inf'))
    fastest_time = sum(fastest_model[1]['times']) / len(fastest_model[1]['times'])
    
    model_names = {'qwen25': 'Qwen 2.5 (3B)', 'gemma3': 'Gemma 3 (4B)', 'ardupilot': 'ArduPilot Stage 1 (270M)'}
    
    print(f"\n🏆 Best Accuracy: {model_names[best_accuracy_model[0]]} - {best_accuracy:.1f}%")
    print(f"⚡ Fastest: {model_names[fastest_model[0]]} - {fastest_time:.3f}s average")
    
    # Recommendation
    print("\n" + "="*100)
    print("RECOMMENDATION")
    print("="*100)
    
    qwen_accuracy = (stats['qwen25']['correct'] / stats['qwen25']['total'] * 100)
    gemma_accuracy = (stats['gemma3']['correct'] / stats['gemma3']['total'] * 100)
    ardupilot_accuracy = (stats['ardupilot']['correct'] / stats['ardupilot']['total'] * 100)
    
    qwen_time = sum(stats['qwen25']['times']) / len(stats['qwen25']['times'])
    gemma_time = sum(stats['gemma3']['times']) / len(stats['gemma3']['times'])
    ardupilot_time = sum(stats['ardupilot']['times']) / len(stats['ardupilot']['times'])
    
    print("\n📊 Performance Summary:")
    print(f"   Qwen 2.5:        {qwen_accuracy:.1f}% accuracy, {qwen_time:.3f}s avg")
    print(f"   Gemma 3:         {gemma_accuracy:.1f}% accuracy, {gemma_time:.3f}s avg")
    print(f"   ArduPilot Stage 1: {ardupilot_accuracy:.1f}% accuracy, {ardupilot_time:.3f}s avg")
    
    print("\n💡 Conclusion:")
    if qwen_accuracy >= 95 and qwen_time < 1.0:
        print("   ✅ RECOMMENDED: Qwen 2.5 (3B)")
        print("   - Excellent accuracy (>95%)")
        print("   - Fast response time (<1s)")
        print("   - Best balance of performance and speed")
    elif gemma_accuracy >= 95:
        print("   ✅ RECOMMENDED: Gemma 3 (4B)")
        print("   - Excellent accuracy (>95%)")
        print("   - Reliable performance")
    else:
        print("   ⚠️  Consider fine-tuning or using larger models")
    
    print("\n" + "="*100)
    print("END OF REPORT")
    print("="*100)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_report.py <csv_filename>")
        sys.exit(1)
    
    csv_filename = sys.argv[1]
    analyze_csv(csv_filename)
