#!/usr/bin/env python3
"""
Test script for MultiMahalanobisPanel
"""

import tkinter as tk
from studio.multi_mahalanobis_panel import MultiMahalanobisPanel

def test_panel():
    root = tk.Tk()
    root.title("Multi Mahalanobis Panel Test")
    root.geometry('1000x700')
    
    # Create main frame
    main_frame = tk.Frame(root)
    main_frame.pack(fill='both', expand=True)
    
    # Create panel
    panel = MultiMahalanobisPanel(main_frame)
    panel.main.pack(fill='both', expand=True)
    
    print("Panel created successfully")
    print("Run button text:", panel.run_button['text'])
    print("Number of data sources:", len(panel.data_sources))
    
    # Test manual analysis (bypassing progress dialog)
    def test_analysis():
        print("Starting manual analysis test...")
        
        # Simulate analysis results
        import numpy as np
        panel.results = {}
        
        for source in panel.data_sources:
            # Generate some test data
            np.random.seed(42)
            distances = np.random.normal(2.0, 0.8, 300)
            distances_clean = panel._remove_outliers_iqr(distances)
            cv, kurtosis = panel._calculate_statistical_metrics(distances_clean)
            
            panel.results[source['name']] = {
                'distances': distances,
                'distances_clean': distances_clean,
                'cv': cv,
                'kurtosis': kurtosis,
                'color': source['color'],
                'label': source['label']
            }
            
            print(f"{source['label']}: CV={cv:.3f}, Kurtosis={kurtosis:.3f}")
        
        # Display results
        panel.display_results()
        print("Analysis completed and displayed")
    
    # Add test button
    test_button = tk.Button(root, text="Test Analysis", command=test_analysis)
    test_button.pack(pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    test_panel()