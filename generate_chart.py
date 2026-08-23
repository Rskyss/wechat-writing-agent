import matplotlib.pyplot as plt
import numpy as np

# Set style for premium look
plt.style.use('default')
fig, ax = plt.subplots(figsize=(8, 3.5), dpi=300)

# Data
models = ['GLM-5.1', 'Kimi K2.6', 'DeepSeek V4-Pro']
params = [0.75, 1.1, 1.6]
colors = ['#E2E8F0', '#CBD5E1', '#3B82F6']  # Muted grays for others, vibrant blue for DeepSeek

# Create horizontal bars
bars = ax.barh(models, params, color=colors, height=0.5)

# Add value labels on the bars
for bar in bars:
    width = bar.get_width()
    label_x = width - 0.05 if width > 0.2 else width + 0.05
    align = 'right' if width > 0.2 else 'left'
    color = 'white' if width > 0.2 and bar.get_facecolor() == (0.231, 0.509, 0.964, 1.0) else '#334155'

    ax.text(label_x, bar.get_y() + bar.get_height()/2,
            f'{width}T',
            ha=align, va='center',
            fontweight='bold', fontsize=14, color=color)

# Remove spines
for spine in ax.spines.values():
    spine.set_visible(False)

# Customizing axes
ax.set_xticks([])
ax.tick_params(axis='y', which='both', length=0, labelsize=13, colors='#1E293B')

# Add Title
plt.title('Open Source Models: Total Parameters (Trillions)', loc='left', pad=15, fontsize=14, fontweight='bold', color='#0F172A')

# Adjust layout and save
plt.tight_layout()
plt.savefig('output/deepseek-v4-hands-on/model-size-comparison.png', bbox_inches='tight', transparent=True)
print("Chart generated successfully.")
