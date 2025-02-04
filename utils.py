import streamlit as st
import plotly.graph_objects as go
from models import GridSpecifications, Preset, THRUSTER_SPECS
import json
import plotly.express as px
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
import csv

def create_thrust_chart(specs: GridSpecifications) -> go.Figure:
    """Create a pie chart showing thrust distribution."""
    thrusts = specs.calculate_thrust_by_type()
    labels = ['Atmospheric', 'Ion', 'Hydrogen']
    values = [thrusts['atmospheric'], thrusts['ion'], thrusts['hydrogen']]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=.3,
        marker_colors=['#FF9999', '#66B2FF', '#99FF99']
    )])

    fig.update_layout(
        title="Thrust Distribution",
        showlegend=True,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )

    return fig

def create_comparison_chart(presets: dict[str, Preset]) -> go.Figure:
    """Create a bar chart comparing different grid configurations."""
    data = []

    for name, preset_json in presets.items():
        preset = Preset.load(preset_json)
        specs = preset.specifications
        thrusts = specs.calculate_thrust_by_type()

        data.extend([
            {'Grid': name, 'Thruster Type': 'Atmospheric', 'Thrust (N)': thrusts['atmospheric']},
            {'Grid': name, 'Thruster Type': 'Ion', 'Thrust (N)': thrusts['ion']},
            {'Grid': name, 'Thruster Type': 'Hydrogen', 'Thrust (N)': thrusts['hydrogen']}
        ])

    df = pd.DataFrame(data)

    fig = px.bar(
        df,
        x='Grid',
        y='Thrust (N)',
        color='Thruster Type',
        barmode='group',
        color_discrete_map={
            'Atmospheric': '#FF9999',
            'Ion': '#66B2FF',
            'Hydrogen': '#99FF99'
        }
    )

    fig.update_layout(
        title="Grid Comparison - Thrust by Type",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )

    return fig

def create_metrics_comparison(presets: dict[str, Preset]) -> go.Figure:
    """Create a radar chart comparing key metrics of different grids."""
    data = []
    categories = ['Total Thrust', 'Lift Capacity', 'TWR']

    for name, preset_json in presets.items():
        preset = Preset.load(preset_json)
        specs = preset.specifications
        total_thrust = specs.calculate_total_thrust()
        lift_capacity = specs.calculate_lift_capacity()
        twr = total_thrust / (specs.mass * specs.gravity)

        # Normalize values for better visualization
        max_thrust = 1e7  # 10 million Newtons as reference
        max_lift = 1e6    # 1 million kg as reference
        max_twr = 10      # 10:1 as reference

        data.append(go.Scatterpolar(
            r=[
                total_thrust / max_thrust,
                lift_capacity / max_lift if lift_capacity > 0 else 0,
                min(twr / max_twr, 1)
            ],
            theta=categories,
            name=name,
            fill='toself'
        ))

    fig = go.Figure(data=data)

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )
        ),
        showlegend=True,
        title="Grid Comparison - Key Metrics",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )

    return fig

def export_grid_to_csv(specs: GridSpecifications) -> io.StringIO:
    """Export grid specifications to CSV format."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(['Space Engineers Grid Specifications'])
    writer.writerow([])

    # Basic specifications
    writer.writerow(['Basic Specifications'])
    writer.writerow(['Mass (kg)', specs.mass])
    writer.writerow(['Gravity (m/s²)', specs.gravity])
    writer.writerow([])

    # Thruster counts
    writer.writerow(['Thruster Configuration'])
    writer.writerow(['Type', 'Small', 'Large'])
    writer.writerow(['Atmospheric', specs.atmospheric_thrusters.small, specs.atmospheric_thrusters.large])
    writer.writerow(['Ion', specs.ion_thrusters.small, specs.ion_thrusters.large])
    writer.writerow(['Hydrogen', specs.hydrogen_thrusters.small, specs.hydrogen_thrusters.large])
    writer.writerow([])

    # Results
    writer.writerow(['Performance Analysis'])
    thrusts = specs.calculate_thrust_by_type()
    total_thrust = specs.calculate_total_thrust()
    lift_capacity = specs.calculate_lift_capacity()

    writer.writerow(['Total Thrust (N)', format_number(total_thrust)])
    for thruster_type, thrust in thrusts.items():
        writer.writerow([f'{thruster_type.title()} Thrust (N)', format_number(thrust)])
    writer.writerow(['Required Hover Thrust (N)', format_number(specs.mass * specs.gravity)])
    writer.writerow(['Lift Capacity (kg)', format_number(lift_capacity)])
    writer.writerow(['Thrust-to-Weight Ratio', format_number(total_thrust / (specs.mass * specs.gravity))])

    output.seek(0)
    return output

def create_pdf_report(specs: GridSpecifications) -> bytes:
    """Create a PDF report of grid specifications."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        spaceAfter=30
    )
    elements.append(Paragraph("Space Engineers Grid Report", title_style))
    elements.append(Spacer(1, 0.2 * inch))

    # Basic Specifications
    elements.append(Paragraph("Basic Specifications", styles['Heading2']))
    basic_data = [
        ['Mass (kg)', format_number(specs.mass)],
        ['Gravity (m/s²)', format_number(specs.gravity)]
    ]
    basic_table = Table(basic_data, colWidths=[2*inch, 2*inch])
    basic_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(basic_table)
    elements.append(Spacer(1, 0.2 * inch))

    # Thruster Configuration
    elements.append(Paragraph("Thruster Configuration", styles['Heading2']))
    thruster_data = [
        ['Type', 'Small', 'Large'],
        ['Atmospheric', str(specs.atmospheric_thrusters.small), str(specs.atmospheric_thrusters.large)],
        ['Ion', str(specs.ion_thrusters.small), str(specs.ion_thrusters.large)],
        ['Hydrogen', str(specs.hydrogen_thrusters.small), str(specs.hydrogen_thrusters.large)]
    ]
    thruster_table = Table(thruster_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
    thruster_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('BACKGROUND', (0, 1), (0, -1), colors.lightgrey),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(thruster_table)
    elements.append(Spacer(1, 0.2 * inch))

    # Performance Analysis
    elements.append(Paragraph("Performance Analysis", styles['Heading2']))
    thrusts = specs.calculate_thrust_by_type()
    total_thrust = specs.calculate_total_thrust()
    lift_capacity = specs.calculate_lift_capacity()

    performance_data = [
        ['Metric', 'Value'],
        ['Total Thrust (N)', format_number(total_thrust)],
        ['Atmospheric Thrust (N)', format_number(thrusts['atmospheric'])],
        ['Ion Thrust (N)', format_number(thrusts['ion'])],
        ['Hydrogen Thrust (N)', format_number(thrusts['hydrogen'])],
        ['Required Hover Thrust (N)', format_number(specs.mass * specs.gravity)],
        ['Lift Capacity (kg)', format_number(lift_capacity)],
        ['Thrust-to-Weight Ratio', format_number(total_thrust / (specs.mass * specs.gravity))]
    ]
    performance_table = Table(performance_data, colWidths=[2.5*inch, 2.5*inch])
    performance_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('BACKGROUND', (0, 1), (0, -1), colors.lightgrey),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(performance_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

def load_css():
    """Load custom CSS."""
    with open('styles.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def save_preset(preset: Preset):
    """Save a preset to session state."""
    if 'presets' not in st.session_state:
        st.session_state.presets = {}
    st.session_state.presets[preset.name] = preset.save()

def load_preset(name: str) -> Preset:
    """Load a preset from session state."""
    if 'presets' not in st.session_state or name not in st.session_state.presets:
        return None
    return Preset.load(st.session_state.presets[name])

def format_number(number: float) -> str:
    """Format a number with thousand separators."""
    return f"{number:,.2f}"

def get_thrust_tooltip(thruster_type: str) -> str:
    """Generate tooltip text for thruster inputs."""
    specs = THRUSTER_SPECS[thruster_type]
    return (
        f"Small: {format_number(specs['small'])}N each\n"
        f"Large: {format_number(specs['large'])}N each"
    )

def get_ai_analysis_tooltip() -> str:
    """Generate tooltip text for AI analysis section."""
    return """
    The AI Analysis provides:
    - Efficiency Assessment: Overall evaluation of your grid's performance
    - Optimization Suggestions: Specific ways to improve your configuration
    - Use Cases: Recommended scenarios for your grid
    - Efficiency Score: 0-100 rating based on thrust distribution and TWR
    - Balance Analysis: Evaluation of thruster type distribution
    """