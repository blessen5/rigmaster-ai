"""
RigMaster AI - Data Flow Diagram Generator
Creates a comprehensive DFD based on the application architecture
"""

from graphviz import Digraph
import os

def create_dfd():
    """Create a comprehensive Data Flow Diagram for RigMaster AI"""
    
    # Create main DFD
    dfd = Digraph('RigMaster_DFD', format='png')
    dfd.attr(rankdir='LR', size='16,12', dpi='300')
    dfd.attr('node', shape='ellipse', style='filled', fillcolor='lightblue', fontname='Arial', fontsize='10')
    dfd.attr('edge', fontname='Arial', fontsize='9')
    
    # External Entities (rectangles)
    dfd.attr('node', shape='rectangle', style='filled', fillcolor='lightgreen')
    dfd.node('User', 'User\n(Customer)', width='1.5')
    dfd.node('Admin', 'Admin\n(Staff)', width='1.5')
    dfd.node('AI_Service', 'AI Service\n(Gemini/Groq/Mistral)', width='1.8')
    dfd.node('Shopping_API', 'Shopping API\n(Google Shopping)', width='1.8')
    dfd.node('Email_Service', 'Email Service\n(SMTP)', width='1.5')
    
    # Processes (circles/ellipses)
    dfd.attr('node', shape='ellipse', style='filled', fillcolor='lightyellow')
    dfd.node('P1', '1.0\nUser\nAuthentication', width='1.5')
    dfd.node('P2', '2.0\nBuild\nConfiguration', width='1.5')
    dfd.node('P3', '3.0\nComponent\nSelection', width='1.5')
    dfd.node('P4', '4.0\nCompatibility\nValidation', width='1.5')
    dfd.node('P5', '5.0\nAI\nRecommendation', width='1.5')
    dfd.node('P6', '6.0\nPrice\nTracking', width='1.5')
    dfd.node('P7', '7.0\nBuild\nManagement', width='1.5')
    dfd.node('P8', '8.0\nPerformance\nAnalysis', width='1.5')
    dfd.node('P9', '9.0\nPassword\nReset', width='1.5')
    dfd.node('P10', '10.0\nAdmin\nManagement', width='1.5')
    dfd.node('P11', '11.0\nShopping\nIntegration', width='1.5')
    dfd.node('P12', '12.0\nBuild\nExport', width='1.5')
    
    # Data Stores (parallel lines)
    dfd.attr('node', shape='cylinder', style='filled', fillcolor='lightcoral')
    dfd.node('DS1', 'D1\nUsers', width='1.2')
    dfd.node('DS2', 'D2\nComponents', width='1.2')
    dfd.node('DS3', 'D3\nSaved Builds', width='1.2')
    dfd.node('DS4', 'D4\nAI Cache', width='1.2')
    dfd.node('DS5', 'D5\nPrice Alerts', width='1.2')
    dfd.node('DS6', 'D6\nShopping Cache', width='1.2')
    dfd.node('DS7', 'D7\nOTPs', width='1.2')
    
    # User flows
    dfd.edge('User', 'P1', label='Login credentials')
    dfd.edge('P1', 'User', label='Auth token')
    dfd.edge('P1', 'DS1', label='Validate user')
    dfd.edge('DS1', 'P1', label='User data')
    
    dfd.edge('User', 'P2', label='Build requirements')
    dfd.edge('P2', 'User', label='Build interface')
    
    dfd.edge('User', 'P3', label='Component selection')
    dfd.edge('P3', 'DS2', label='Query components')
    dfd.edge('DS2', 'P3', label='Component list')
    dfd.edge('P3', 'User', label='Available components')
    
    dfd.edge('P2', 'P4', label='Selected components')
    dfd.edge('P4', 'DS2', label='Check compatibility')
    dfd.edge('DS2', 'P4', label='Component specs')
    dfd.edge('P4', 'User', label='Validation results')
    
    dfd.edge('User', 'P5', label='Budget & preferences')
    dfd.edge('P5', 'AI_Service', label='AI request')
    dfd.edge('AI_Service', 'P5', label='AI response')
    dfd.edge('P5', 'DS4', label='Cache result')
    dfd.edge('DS4', 'P5', label='Cached data')
    dfd.edge('P5', 'DS2', label='Query components')
    dfd.edge('DS2', 'P5', label='Component data')
    dfd.edge('P5', 'User', label='Recommendations')
    
    dfd.edge('User', 'P6', label='Set price alert')
    dfd.edge('P6', 'DS5', label='Store alert')
    dfd.edge('DS5', 'P6', label='Alert data')
    dfd.edge('P6', 'DS2', label='Check prices')
    dfd.edge('DS2', 'P6', label='Current prices')
    dfd.edge('P6', 'User', label='Price notifications')
    
    dfd.edge('User', 'P7', label='Save/Load build')
    dfd.edge('P7', 'DS3', label='Store build')
    dfd.edge('DS3', 'P7', label='Build data')
    dfd.edge('P7', 'User', label='Saved builds')
    
    dfd.edge('User', 'P8', label='Request analysis')
    dfd.edge('P8', 'DS3', label='Get build')
    dfd.edge('DS3', 'P8', label='Build config')
    dfd.edge('P8', 'DS2', label='Component specs')
    dfd.edge('DS2', 'P8', label='Technical data')
    dfd.edge('P8', 'User', label='Performance report')
    
    dfd.edge('User', 'P9', label='Reset request')
    dfd.edge('P9', 'DS1', label='Verify email')
    dfd.edge('DS1', 'P9', label='User email')
    dfd.edge('P9', 'DS7', label='Store OTP')
    dfd.edge('DS7', 'P9', label='OTP data')
    dfd.edge('P9', 'Email_Service', label='Send OTP')
    dfd.edge('Email_Service', 'User', label='OTP email')
    dfd.edge('User', 'P9', label='Verify OTP')
    dfd.edge('P9', 'User', label='Reset confirmation')
    
    dfd.edge('User', 'P11', label='Request shopping')
    dfd.edge('P11', 'DS6', label='Check cache')
    dfd.edge('DS6', 'P11', label='Cached listings')
    dfd.edge('P11', 'Shopping_API', label='Search products')
    dfd.edge('Shopping_API', 'P11', label='Product listings')
    dfd.edge('P11', 'DS6', label='Cache results')
    dfd.edge('P11', 'User', label='Shopping links')
    
    dfd.edge('User', 'P12', label='Export request')
    dfd.edge('P12', 'DS3', label='Get build')
    dfd.edge('DS3', 'P12', label='Build data')
    dfd.edge('P12', 'User', label='PDF report')
    
    # Admin flows
    dfd.edge('Admin', 'P1', label='Admin login')
    dfd.edge('P1', 'Admin', label='Admin access')
    
    dfd.edge('Admin', 'P10', label='Manage system')
    dfd.edge('P10', 'DS1', label='User CRUD')
    dfd.edge('DS1', 'P10', label='User list')
    dfd.edge('P10', 'DS2', label='Component CRUD')
    dfd.edge('DS2', 'P10', label='Component list')
    dfd.edge('P10', 'Admin', label='Admin dashboard')
    
    # Save the diagram
    output_file = 'RigMaster_DFD_Level0'
    dfd.render(output_file, cleanup=True)
    print(f"[SUCCESS] DFD Level 0 created: {output_file}.png")
    
    return output_file

def create_context_diagram():
    """Create a Context Diagram (Level 0)"""
    
    context = Digraph('RigMaster_Context', format='png')
    context.attr(rankdir='TB', size='12,10', dpi='300')
    context.attr('node', fontname='Arial', fontsize='11')
    context.attr('edge', fontname='Arial', fontsize='10')
    
    # Central system
    context.attr('node', shape='circle', style='filled', fillcolor='lightblue', width='3', height='3')
    context.node('System', 'RigMaster AI\nPC Building\nSystem', fontsize='14')
    
    # External entities
    context.attr('node', shape='rectangle', style='filled', fillcolor='lightgreen', width='2', height='1')
    context.node('User', 'User/Customer')
    context.node('Admin', 'Administrator')
    context.node('AI', 'AI Services\n(Gemini/Groq/Mistral)')
    context.node('Shopping', 'Shopping API\n(Google Shopping)')
    context.node('Email', 'Email Service')
    
    # Data flows
    context.edge('User', 'System', label='Login, Build Config,\nComponent Selection,\nPrice Alerts')
    context.edge('System', 'User', label='Recommendations,\nValidation Results,\nSaved Builds, Reports')
    
    context.edge('Admin', 'System', label='User Management,\nComponent Management,\nSystem Config')
    context.edge('System', 'Admin', label='Admin Dashboard,\nSystem Analytics')
    
    context.edge('System', 'AI', label='Build Requirements,\nUser Preferences')
    context.edge('AI', 'System', label='AI Recommendations,\nPerformance Predictions')
    
    context.edge('System', 'Shopping', label='Component Search\nQueries')
    context.edge('Shopping', 'System', label='Product Listings,\nPrices')
    
    context.edge('System', 'Email', label='OTP, Notifications')
    context.edge('Email', 'User', label='Password Reset Email')
    
    # Save
    output_file = 'RigMaster_Context_Diagram'
    context.render(output_file, cleanup=True)
    print(f"[SUCCESS] Context Diagram created: {output_file}.png")
    
    return output_file

def create_level1_dfd():
    """Create detailed Level 1 DFD"""
    
    dfd1 = Digraph('RigMaster_DFD_Level1', format='png')
    dfd1.attr(rankdir='TB', size='18,14', dpi='300')
    dfd1.attr('node', fontname='Arial', fontsize='9')
    dfd1.attr('edge', fontname='Arial', fontsize='8')
    
    # Group processes by subsystem
    with dfd1.subgraph(name='cluster_auth') as c:
        c.attr(label='Authentication Subsystem', style='filled', fillcolor='lightgray')
        c.attr('node', shape='ellipse', style='filled', fillcolor='lightyellow')
        c.node('P1_1', '1.1\nLogin')
        c.node('P1_2', '1.2\nSignup')
        c.node('P1_3', '1.3\nLogout')
        c.node('P1_4', '1.4\nSession\nManagement')
    
    with dfd1.subgraph(name='cluster_build') as c:
        c.attr(label='Build Management Subsystem', style='filled', fillcolor='lightgray')
        c.attr('node', shape='ellipse', style='filled', fillcolor='lightyellow')
        c.node('P2_1', '2.1\nCreate Build')
        c.node('P2_2', '2.2\nEdit Build')
        c.node('P2_3', '2.3\nDelete Build')
        c.node('P2_4', '2.4\nView Builds')
    
    with dfd1.subgraph(name='cluster_component') as c:
        c.attr(label='Component Management', style='filled', fillcolor='lightgray')
        c.attr('node', shape='ellipse', style='filled', fillcolor='lightyellow')
        c.node('P3_1', '3.1\nBrowse\nComponents')
        c.node('P3_2', '3.2\nSearch\nComponents')
        c.node('P3_3', '3.3\nFilter by\nCategory')
    
    with dfd1.subgraph(name='cluster_validation') as c:
        c.attr(label='Validation Subsystem', style='filled', fillcolor='lightgray')
        c.attr('node', shape='ellipse', style='filled', fillcolor='lightyellow')
        c.node('P4_1', '4.1\nCheck CPU\nCompatibility')
        c.node('P4_2', '4.2\nCheck RAM\nCompatibility')
        c.node('P4_3', '4.3\nCalculate\nPower')
        c.node('P4_4', '4.4\nValidate\nBuild')
    
    # External entities
    dfd1.attr('node', shape='rectangle', style='filled', fillcolor='lightgreen')
    dfd1.node('User', 'User')
    dfd1.node('Admin', 'Admin')
    
    # Data stores
    dfd1.attr('node', shape='cylinder', style='filled', fillcolor='lightcoral')
    dfd1.node('DS_Users', 'D1: Users')
    dfd1.node('DS_Components', 'D2: Components')
    dfd1.node('DS_Builds', 'D3: Saved Builds')
    
    # Key flows
    dfd1.edge('User', 'P1_1', label='Credentials')
    dfd1.edge('P1_1', 'DS_Users', label='Validate')
    dfd1.edge('DS_Users', 'P1_1', label='User data')
    dfd1.edge('P1_1', 'P1_4', label='Create session')
    
    dfd1.edge('User', 'P2_1', label='Build data')
    dfd1.edge('P2_1', 'P4_4', label='Validate')
    dfd1.edge('P4_4', 'DS_Components', label='Check specs')
    dfd1.edge('P4_4', 'P2_1', label='Validation result')
    dfd1.edge('P2_1', 'DS_Builds', label='Save')
    
    dfd1.edge('User', 'P3_1', label='Browse request')
    dfd1.edge('P3_1', 'DS_Components', label='Query')
    dfd1.edge('DS_Components', 'P3_1', label='Component list')
    dfd1.edge('P3_1', 'User', label='Display')
    
    # Save
    output_file = 'RigMaster_DFD_Level1'
    dfd1.render(output_file, cleanup=True)
    print(f"[SUCCESS] DFD Level 1 created: {output_file}.png")
    
    return output_file

if __name__ == "__main__":
    print("Generating RigMaster AI Data Flow Diagrams...")
    print("=" * 60)
    
    # Create all diagrams
    context_file = create_context_diagram()
    level0_file = create_dfd()
    level1_file = create_level1_dfd()
    
    print("=" * 60)
    print("All DFD diagrams created successfully!")
    print(f"\n1. Context Diagram: {context_file}.png")
    print(f"2. Level 0 DFD: {level0_file}.png")
    print(f"3. Level 1 DFD: {level1_file}.png")
