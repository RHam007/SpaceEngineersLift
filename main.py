import streamlit as st
import numpy as np
from utils import (
    create_thrust_chart, create_comparison_chart, create_metrics_comparison,
    load_css, save_preset, load_preset, format_number, get_thrust_tooltip,
    export_grid_to_csv, create_pdf_report, get_ai_analysis_tooltip
)
from models import GridSpecifications, Preset, ThrusterCount
from block_specs import BLOCK_MASSES, calculate_total_mass
from ai_assistant import ThrusterAIAssistant

def create_thruster_inputs(title: str, key_prefix: str, help_text: str):
    """Create number inputs for small and large thrusters of a specific type."""
    st.markdown(f"#### {title}")
    col1, col2 = st.columns(2)

    with col1:
        small = st.number_input(
            "Small",
            min_value=0,
            value=0,
            step=1,
            key=f"{key_prefix}_small",
            help=help_text
        )

    with col2:
        large = st.number_input(
            "Large",
            min_value=0,
            value=0,
            step=1,
            key=f"{key_prefix}_large",
            help=help_text
        )

    return ThrusterCount(small=small, large=large)

def create_block_inputs(block_type: str, block_specs: dict, key_prefix: str):
    """Create number inputs for small and large blocks of a specific type."""
    col1, col2 = st.columns(2)

    with col1:
        small = st.number_input(
            "Small",
            min_value=0,
            value=0,
            step=1,
            key=f"{key_prefix}_small",
            help=f"Mass: {format_number(block_specs['small'])} kg each"
        )

    with col2:
        large = st.number_input(
            "Large",
            min_value=0,
            value=0,
            step=1,
            key=f"{key_prefix}_large",
            help=f"Mass: {format_number(block_specs['large'])} kg each"
        )

    return small, large

def show_ai_analysis(specs: GridSpecifications):
    """Display AI analysis of the grid configuration."""
    st.subheader("🤖 AI Analysis")
    st.info(get_ai_analysis_tooltip())

    try:
        with st.spinner("Analyzing grid configuration..."):
            ai_assistant = ThrusterAIAssistant()
            analysis = ai_assistant.analyze_grid(specs)
            suggestions = ai_assistant.suggest_improvements(specs)

            st.markdown('<div class="ai-analysis">', unsafe_allow_html=True)

            # Display efficiency assessment
            st.markdown("#### 📊 Efficiency Assessment")
            st.markdown(analysis["efficiency"])

            # Display optimization suggestions
            st.markdown("#### 🔧 Optimization Suggestions")
            st.markdown(analysis["optimization"])

            # Display use case analysis
            st.markdown("#### 🎯 Recommended Use Cases")
            st.markdown(analysis["use_cases"])

            # Display efficiency score
            score = suggestions["efficiency_score"]
            st.markdown('<div class="efficiency-score">', unsafe_allow_html=True)
            st.metric("Grid Efficiency Score", f"{score:.1f}/100", 
                     help="Score based on thrust distribution and TWR")
            st.markdown('</div>', unsafe_allow_html=True)

            # Display specific suggestions
            st.markdown("#### 💡 Suggested Improvements")
            for suggestion in suggestions["suggested_changes"]:
                st.markdown(f'<div class="suggestion-item">• {suggestion}</div>', 
                          unsafe_allow_html=True)

            # Display thrust balance analysis
            st.markdown('<div class="balance-info">', unsafe_allow_html=True)
            st.info(suggestions["thrust_balance"])
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"""
        Unable to generate AI analysis at this time. 
        Please check your configuration and try again.
        Error: {str(e)}
        """)
        st.warning("""
        Tips:
        - Ensure you have entered valid grid specifications
        - Check if all thruster counts are non-negative
        - Verify that the grid mass is greater than zero
        """)

def main():
    st.set_page_config(
        page_title="Space Engineers Lift Calculator",
        page_icon="🚀",
        layout="wide"
    )

    load_css()

    st.title("🚀 Space Engineers Lift Calculator")
    st.markdown("""
    Calculate the lift capacity of your Space Engineers grid based on thruster configuration
    and mass. Input your grid specifications below to get started.
    """)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Grid Specifications")

        # Mass input tabs
        mass_tab1, mass_tab2 = st.tabs(["Manual Mass Input", "Block Calculator"])

        with mass_tab1:
            mass = st.number_input(
                "Grid Mass (kg)",
                min_value=0.0,
                value=1000.0,
                step=100.0,
                help="Total mass of your grid in kilograms"
            )

        with mass_tab2:
            st.markdown("#### Block Configuration")
            block_counts = {}

            # Armor blocks
            st.markdown("##### Armor Blocks")
            for block_type in ['light_armor_block', 'heavy_armor_block']:
                display_name = block_type.replace('_', ' ').title()
                block_counts[block_type] = create_block_inputs(
                    block_type,
                    BLOCK_MASSES[block_type],
                    f"block_{block_type}"
                )

            # Structural blocks
            st.markdown("##### Structural Blocks")
            for block_type in ['steel_plate', 'interior_plate']:
                display_name = block_type.replace('_', ' ').title()
                block_counts[block_type] = create_block_inputs(
                    block_type,
                    BLOCK_MASSES[block_type],
                    f"block_{block_type}"
                )

            # Functional blocks
            st.markdown("##### Functional Blocks")
            for block_type in ['cargo_container', 'refinery', 'assembler', 'reactor']:
                display_name = block_type.replace('_', ' ').title()
                block_counts[block_type] = create_block_inputs(
                    block_type,
                    BLOCK_MASSES[block_type],
                    f"block_{block_type}"
                )

            calculated_mass = calculate_total_mass(block_counts)
            st.markdown(f"#### Calculated Mass: {format_number(calculated_mass)} kg")

            if st.button("Use Calculated Mass"):
                mass = calculated_mass
                st.experimental_rerun()

        gravity = st.number_input(
            "Gravity (m/s²)",
            min_value=0.0,
            value=9.81,
            step=0.1,
            help="Local gravity in m/s². Earth is 9.81 m/s²"
        )

        st.subheader("Thruster Configuration")
        st.markdown("Enter the number of thrusters by size:")

        atmospheric = create_thruster_inputs(
            "Atmospheric Thrusters",
            "atmo",
            get_thrust_tooltip('atmospheric')
        )

        ion = create_thruster_inputs(
            "Ion Thrusters",
            "ion",
            get_thrust_tooltip('ion')
        )

        hydrogen = create_thruster_inputs(
            "Hydrogen Thrusters",
            "hydro",
            get_thrust_tooltip('hydrogen')
        )

        specs = GridSpecifications(
            mass=mass,
            gravity=gravity,
            atmospheric_thrusters=atmospheric,
            ion_thrusters=ion,
            hydrogen_thrusters=hydrogen
        )

        if st.button("Calculate"):
            st.session_state.calculated = True
            st.session_state.current_specs = specs

    with col2:
        st.subheader("Presets")

        preset_name = st.text_input("Preset Name", key="preset_name")

        if st.button("Save Current"):
            if preset_name:
                preset = Preset(preset_name, specs)
                save_preset(preset)
                st.success(f"Saved preset: {preset_name}")
            else:
                st.error("Please enter a preset name")

        if 'presets' in st.session_state and st.session_state.presets:
            selected_preset = st.selectbox(
                "Load Preset",
                options=list(st.session_state.presets.keys())
            )

            if st.button("Load"):
                preset = load_preset(selected_preset)
                if preset:
                    st.session_state.current_specs = preset.specifications
                    st.experimental_rerun()

    if 'calculated' in st.session_state and st.session_state.calculated:
        st.header("Results")

        results_col1, results_col2 = st.columns(2)

        with results_col1:
            st.markdown("### Thrust Analysis")
            total_thrust = specs.calculate_total_thrust()
            thrust_by_type = specs.calculate_thrust_by_type()
            lift_capacity = specs.calculate_lift_capacity()

            st.markdown(f"""
            <div class="result-container">
                <p>Total Thrust: {format_number(total_thrust)} N</p>
                <p>Atmospheric Thrust: {format_number(thrust_by_type['atmospheric'])} N</p>
                <p>Ion Thrust: {format_number(thrust_by_type['ion'])} N</p>
                <p>Hydrogen Thrust: {format_number(thrust_by_type['hydrogen'])} N</p>
                <p>Required Hover Thrust: {format_number(mass * gravity)} N</p>
                <p>Lift Capacity: {format_number(lift_capacity)} kg</p>
                <p>Thrust-to-Weight Ratio: {format_number(total_thrust / (mass * gravity))}</p>
            </div>
            """, unsafe_allow_html=True)

            # Export buttons for current grid
            st.subheader("Export Results")
            export_col1, export_col2 = st.columns(2)

            with export_col1:
                csv_data = export_grid_to_csv(specs)
                st.download_button(
                    label="Download CSV",
                    data=csv_data.getvalue(),
                    file_name="grid_specifications.csv",
                    mime="text/csv"
                )

            with export_col2:
                pdf_data = create_pdf_report(specs)
                st.download_button(
                    label="Download PDF",
                    data=pdf_data,
                    file_name="grid_report.pdf",
                    mime="application/pdf"
                )

        with results_col2:
            st.plotly_chart(create_thrust_chart(specs), use_container_width=True)

        #Added AI analysis section here
        st.header("AI Analysis")
        with st.expander("Show AI Analysis", expanded=True):
            show_ai_analysis(specs)


    # Grid Comparison Section
    if 'presets' in st.session_state and len(st.session_state.presets) > 1:
        st.header("Grid Comparisons")
        st.markdown("""
        Compare different grid configurations side by side. Save multiple grid setups
        as presets to enable comparison.
        """)

        comparison_col1, comparison_col2 = st.columns(2)

        with comparison_col1:
            st.plotly_chart(
                create_comparison_chart(st.session_state.presets),
                use_container_width=True
            )

        with comparison_col2:
            st.plotly_chart(
                create_metrics_comparison(st.session_state.presets),
                use_container_width=True
            )

if __name__ == "__main__":
    main()