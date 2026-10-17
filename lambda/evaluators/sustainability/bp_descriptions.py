"""
Best Practice Descriptions from AWS Well-Architected Framework
"""

PERFORMANCE_BP_DESCRIPTIONS = {
    'PERF01-BP01': 'Learn about and understand available cloud services and features',
    'PERF01-BP02': 'Use guidance from your cloud provider or an appropriate partner',
    'PERF01-BP03': 'Factor cost into architectural decisions',
    'PERF01-BP04': 'Evaluate how trade-offs impact customers and architecture efficiency',
    'PERF01-BP05': 'Use policies and reference architectures',
    'PERF01-BP06': 'Use benchmarking to drive architectural decisions',
    'PERF01-BP07': 'Use a data-driven approach for architectural choices',
    
    'PERF02-BP01': 'Select the best compute options for your workload',
    'PERF02-BP02': 'Understand the available compute configuration and features',
    'PERF02-BP03': 'Collect compute-related metrics',
    'PERF02-BP04': 'Configure and right-size compute resources',
    'PERF02-BP05': 'Scale your compute resources dynamically',
    'PERF02-BP06': 'Use optimized hardware-based compute accelerators',
    
    'PERF03-BP01': 'Use a purpose-built data store',
    'PERF03-BP02': 'Evaluate available configuration options for data store',
    'PERF03-BP03': 'Collect and record data store performance metrics',
    'PERF03-BP04': 'Implement strategies to improve query performance',
    'PERF03-BP05': 'Implement data access patterns that utilize caching',
    
    'PERF04-BP01': 'Understand how networking impacts performance',
    'PERF04-BP02': 'Evaluate available networking features',
    'PERF04-BP03': 'Choose appropriate dedicated connectivity or VPN',
    'PERF04-BP04': 'Use load balancing to distribute traffic',
    'PERF04-BP05': 'Choose network protocols to improve performance',
    'PERF04-BP06': 'Choose workload location based on network requirements',
    'PERF04-BP07': 'Optimize network configuration based on metrics',
    
    'PERF05-BP01': 'Establish key performance indicators (KPIs)',
    'PERF05-BP02': 'Use monitoring solutions',
    'PERF05-BP03': 'Define a process to improve workload performance',
    'PERF05-BP04': 'Load test your workload',
    'PERF05-BP05': 'Use automation to proactively remediate issues',
    'PERF05-BP06': 'Keep your workload and services up-to-date',
    'PERF05-BP07': 'Review metrics at regular intervals',
}

COST_BP_DESCRIPTIONS = {
    'COST01-BP01': 'Establish ownership of cost optimization',
    'COST01-BP02': 'Establish a partnership between finance and technology',
    'COST01-BP03': 'Establish cloud budgets and forecasts',
    'COST01-BP04': 'Implement cost awareness in organizational processes',
    'COST01-BP05': 'Report and notify on cost optimization',
    'COST01-BP06': 'Monitor cost proactively',
    'COST01-BP07': 'Keep up-to-date with new service releases',
    'COST01-BP08': 'Create a cost-aware culture',
    'COST01-BP09': 'Quantify business value from cost optimization',
    
    'COST02-BP01': 'Develop policies based on your organization requirements',
    'COST02-BP02': 'Implement goals and targets',
    'COST02-BP03': 'Implement an account structure',
    'COST02-BP04': 'Implement groups and roles',
    'COST02-BP05': 'Implement cost controls',
    'COST02-BP06': 'Track project lifecycle',
    
    'COST03-BP01': 'Configure detailed information sources',
    'COST03-BP02': 'Add organization information to cost and usage',
    'COST03-BP03': 'Identify cost attribution categories',
    'COST03-BP04': 'Establish organization metrics',
    'COST03-BP05': 'Configure billing and cost management tools',
    'COST03-BP06': 'Allocate costs based on workload metrics',
    
    'COST04-BP01': 'Track resources over their lifetime',
    'COST04-BP02': 'Implement a decommissioning process',
    'COST04-BP03': 'Decommission resources',
    'COST04-BP04': 'Decommission resources automatically',
    'COST04-BP05': 'Enforce data retention policies',
    
    'COST05-BP01': 'Identify organization requirements for cost',
    'COST05-BP02': 'Analyze all components of the workload',
    'COST05-BP03': 'Perform a thorough analysis of each component',
    'COST05-BP04': 'Select software with cost-effective licensing',
    'COST05-BP05': 'Select components to optimize cost',
    'COST05-BP06': 'Perform cost analysis for different usage over time',
    
    'COST06-BP01': 'Perform cost modeling',
    'COST06-BP02': 'Select resource type, size, and number based on data',
    'COST06-BP03': 'Select resource type automatically based on metrics',
    'COST06-BP04': 'Consider using shared resources',
    
    'COST07-BP01': 'Perform pricing model analysis',
    'COST07-BP02': 'Choose Regions based on cost',
    'COST07-BP03': 'Select third-party agreements with cost-efficient terms',
    'COST07-BP04': 'Implement pricing models for all components',
    'COST07-BP05': 'Perform pricing model analysis at management account level',
    
    'COST08-BP01': 'Perform data transfer modeling',
    'COST08-BP02': 'Select components to optimize data transfer cost',
    'COST08-BP03': 'Implement services to reduce data transfer costs',
    
    'COST09-BP01': 'Perform an analysis on the workload demand',
    'COST09-BP02': 'Implement a buffer or throttle to manage demand',
    'COST09-BP03': 'Supply resources dynamically',
    
    'COST10-BP01': 'Develop a workload review process',
    'COST10-BP02': 'Review and analyze this workload regularly',
    
    'COST11-BP01': 'Perform automation for operations',
}

OPERATIONAL_EXCELLENCE_BP_DESCRIPTIONS = {
    # OPS01: Priorities (6 BPs)
    'OPS01-BP01': 'Evaluate external customer needs',
    'OPS01-BP02': 'Evaluate internal customer needs',
    'OPS01-BP03': 'Evaluate governance requirements',
    'OPS01-BP04': 'Evaluate compliance requirements',
    'OPS01-BP05': 'Evaluate threat landscape',
    'OPS01-BP06': 'Evaluate tradeoffs while managing benefits and risks',
    
    # OPS02: Organization structure (2 BPs)
    'OPS02-BP01': 'Resources have identified owners',
    'OPS02-BP02': 'Processes and procedures have identified owners',
    
    # OPS03: Organizational culture (3 BPs)
    'OPS03-BP01': 'Executive sponsorship',
    'OPS03-BP02': 'Team members are empowered to take action when outcomes are at risk',
    'OPS03-BP03': 'Escalation is encouraged',
    
    # OPS04: Observability (4 BPs)
    'OPS04-BP01': 'Identify key performance indicators',
    'OPS04-BP02': 'Implement application telemetry',
    'OPS04-BP03': 'Implement user experience telemetry',
    'OPS04-BP04': 'Implement dependency telemetry',
    
    # OPS05: Reduce defects (4 BPs)
    'OPS05-BP01': 'Use version control',
    'OPS05-BP02': 'Test and validate changes',
    'OPS05-BP03': 'Use configuration management systems',
    'OPS05-BP04': 'Use build and deployment management systems',
    
    # OPS06: Mitigate deployment risks (4 BPs)
    'OPS06-BP01': 'Plan for unsuccessful changes',
    'OPS06-BP02': 'Test deployments',
    'OPS06-BP03': 'Employ safe deployment strategies',
    'OPS06-BP04': 'Automate testing and rollback',
    
    # OPS07: Readiness (2 BPs)
    'OPS07-BP01': 'Ensure personnel capability',
    'OPS07-BP02': 'Ensure consistent review of operational readiness',
    
    # OPS08: Utilize observability (2 BPs)
    'OPS08-BP01': 'Analyze workload metrics',
    'OPS08-BP02': 'Analyze workload logs',
    
    # OPS09: Operations health (2 BPs)
    'OPS09-BP01': 'Measure operations goals and KPIs',
    'OPS09-BP02': 'Communicate status and trends',
    
    # OPS10: Manage events (1 BP)
    'OPS10-BP01': 'Use a process for event, incident, and problem management',
    
    # OPS11: Evolve operations (1 BP)
    'OPS11-BP01': 'Have a process for continuous improvement',
}

RELIABILITY_BP_DESCRIPTIONS = {
    # REL01: Service Quotas and constraints (6 BPs)
    'REL01-BP01': 'Aware of service quotas and constraints',
    'REL01-BP02': 'Manage service quotas across accounts and regions',
    'REL01-BP03': 'Accommodate fixed service quotas and constraints through architecture',
    'REL01-BP04': 'Monitor and manage quotas',
    'REL01-BP05': 'Automate quota management',
    'REL01-BP06': 'Ensure that a sufficient gap exists between the current quotas and the maximum usage to accommodate failover',
    
    # REL02: Network topology (3 BPs)
    'REL02-BP01': 'Use highly available network connectivity for your workload public endpoints',
    'REL02-BP02': 'Provision redundant connectivity between private networks in the cloud and on-premises environments',
    'REL02-BP03': 'Ensure IP subnet allocation accounts for expansion and availability',
    
    # REL03: Service architecture (3 BPs)
    'REL03-BP01': 'Choose how to segment your workload',
    'REL03-BP02': 'Build services focused on specific business domains and functionality',
    'REL03-BP03': 'Provide service contracts per API',
    
    # REL04: Prevent failures in distributed systems (4 BPs)
    'REL04-BP01': 'Identify which kind of distributed system is required',
    'REL04-BP02': 'Implement loosely coupled dependencies',
    'REL04-BP03': 'Make all responses idempotent',
    'REL04-BP04': 'Do constant work',
    
    # REL05: Mitigate failures in distributed systems (2 BPs)
    'REL05-BP01': 'Implement graceful degradation to transform applicable hard dependencies into soft dependencies',
    'REL05-BP02': 'Throttle requests',
    
    # REL06: Monitor workload resources (3 BPs)
    'REL06-BP01': 'Monitor all components for the workload (Generation)',
    'REL06-BP02': 'Define and calculate metrics (Aggregation)',
    'REL06-BP03': 'Send notifications (Real-time processing and alarming)',
    
    # REL07: Adapt to changes in demand (2 BPs)
    'REL07-BP01': 'Use automation when obtaining or scaling resources',
    'REL07-BP02': 'Obtain resources upon detection of impairment to a workload',
    
    # REL08: Implement change (4 BPs)
    'REL08-BP01': 'Use runbooks for standard activities such as deployment',
    'REL08-BP02': 'Integrate functional testing as part of your deployment',
    'REL08-BP03': 'Integrate resiliency testing as part of your deployment',
    'REL08-BP04': 'Deploy using immutable infrastructure',
    
    # REL09: Back up data (4 BPs)
    'REL09-BP01': 'Identify and back up all data that needs to be backed up, or reproduce the data from sources',
    'REL09-BP02': 'Secure and encrypt backups',
    'REL09-BP03': 'Perform data backup automatically',
    'REL09-BP04': 'Perform periodic recovery of the data to verify backup integrity and processes',
    
    # REL10: Fault isolation (2 BPs)
    'REL10-BP01': 'Deploy the workload to multiple locations',
    'REL10-BP02': 'Select the appropriate locations for your multi-location deployment',
    
    # REL11: Withstand component failures (7 BPs)
    'REL11-BP01': 'Monitor all components of the workload to detect failures',
    'REL11-BP02': 'Fail over to healthy resources',
    'REL11-BP03': 'Automate healing on all layers',
    'REL11-BP04': 'Rely on the data plane and not the control plane during recovery',
    'REL11-BP05': 'Use static stability to prevent bimodal behavior',
    'REL11-BP06': 'Send notifications when events impact availability',
    'REL11-BP07': 'Architect your product to meet availability targets and uptime service level agreements (SLAs)',
    
    # REL12: Test reliability (3 BPs)
    'REL12-BP01': 'Use playbooks to investigate failures',
    'REL12-BP02': 'Perform post-incident analysis',
    'REL12-BP03': 'Test functional requirements',
    
    # REL13: Plan for disaster recovery (4 BPs)
    'REL13-BP01': 'Define recovery objectives for downtime and data loss',
    'REL13-BP02': 'Use defined recovery strategies to meet the recovery objectives',
    'REL13-BP03': 'Test disaster recovery implementation to validate the implementation',
    'REL13-BP04': 'Manage configuration drift at the DR site or region',
}

SUSTAINABILITY_BP_DESCRIPTIONS = {
    # SUS01: Region selection (1 BP)
    'SUS01-BP01': 'Choose Region based on both business requirements and sustainability goals',
    
    # SUS02: Alignment to demand (6 BPs)
    'SUS02-BP01': 'Scale workload infrastructure dynamically',
    'SUS02-BP02': 'Align SLAs with sustainability goals',
    'SUS02-BP03': 'Stop the creation and maintenance of unused assets',
    'SUS02-BP04': 'Optimize geographic placement of workloads based on their networking requirements',
    'SUS02-BP05': 'Optimize team member resources for activities performed',
    'SUS02-BP06': 'Implement buffering or throttling to flatten the demand curve',
    
    # SUS03: Software and architecture patterns (5 BPs)
    'SUS03-BP01': 'Optimize software and architecture for asynchronous and scheduled jobs',
    'SUS03-BP02': 'Remove or refactor workload components with low or no use',
    'SUS03-BP03': 'Optimize areas of code that consume the most time or resources',
    'SUS03-BP04': 'Optimize impact on devices and equipment',
    'SUS03-BP05': 'Use software patterns and architectures that best support data access and storage patterns',
    
    # SUS04: Data management (8 BPs)
    'SUS04-BP01': 'Implement a data classification policy',
    'SUS04-BP02': 'Use technologies that support data access and storage patterns',
    'SUS04-BP03': 'Use policies to manage the lifecycle of your datasets',
    'SUS04-BP04': 'Use elasticity and automation to expand block storage or file system',
    'SUS04-BP05': 'Remove unneeded or redundant data',
    'SUS04-BP06': 'Use shared file systems or storage to access common data',
    'SUS04-BP07': 'Minimize data movement across networks',
    'SUS04-BP08': 'Back up data only when difficult to recreate',
    
    # SUS05: Hardware and services (4 BPs)
    'SUS05-BP01': 'Use the minimum amount of hardware to meet your needs',
    'SUS05-BP02': 'Use instance types with the least impact',
    'SUS05-BP03': 'Use managed services',
    'SUS05-BP04': 'Optimize your use of hardware-based compute accelerators',
    
    # SUS06: Organizational processes (5 BPs)
    'SUS06-BP01': 'Communicate and cascade your sustainability goals',
    'SUS06-BP02': 'Adopt methods that can rapidly introduce sustainability improvements',
    'SUS06-BP03': 'Keep your workload up-to-date',
    'SUS06-BP04': 'Increase utilization of build environments',
    'SUS06-BP05': 'Use managed device farms for testing',
}
