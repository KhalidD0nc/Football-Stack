

# Abstract

In modern football, data-driven tactical intelligence has become a cornerstone of competitive success, yet a significant technological disparity exists between professional clubs and amateur coaching environments. While elite teams leverage specialized analytics departments and advanced infrastructure to optimize strategic decision-making, grassroots coaches are largely restricted to basic descriptive statistics or labor-intensive manual video reviews. Existing automated solutions primarily focus on broadcast summarization for spectator entertainment, identifying what happened during a match but failing to explain why it happened or how coaches can develop tactical countermeasures. To address this critical gap, this project proposes an **AI-Powered Coaching Platform** designed to democratize access to elite-level sports analytics for coaching staff at all levels. By integrating lightweight **Computer Vision (CV)** for tactical event extraction, **Machine Learning** for predictive analytics, and **autonomous AI agents** for opponent analysis and talent scouting, the proposed solution autonomously processes raw match footage and fragmented data sources to deliver actionable strategic intelligence. Unlike conventional tools, this platform is engineered specifically for **coaching decision support**, shifting from passive observation to active tactical assistance by providing diagnostic match feedback, opponent intelligence reports, and data-driven recruitment recommendations through an integrated dashboard and interactive natural language interface. This report documents the foundational phase of the project, encompassing a comprehensive literature review, requirements elicitation, and architectural design, ultimately defining the functional specifications necessary to translate unstructured video data into a **unified coaching command center** for tactical preparation, squad management, and strategic planning.

Table of Contents

[***List of Figures	5***](#list-of-figures)

[***List of Tables	6***](#heading)

[***List of Abbreviations	7***](#list-of-abbreviations)

[***Chapter 1: Introduction	8***](#chapter-1:-introduction)

[**1.1 Overview	8**](#1.1-overview)

[**1.2 Problem Definition	8**](#1.2-problem-definition)

[**1.3 Aims and Objectives	9**](#1.3-aims-and-objectives)

[**1.4 Project Timeline	11**](#1.4-project-timeline)

[**1.6 Conclusions	15**](#1.6-conclusions)

[***Chapter 2: Literature Review Chapter	16***](#chapter-2:-literature-review-chapter)

[**2.1 Introduction	16**](#2.1-introduction)

[**2.2 Background	16**](#2.2-background)  
[2.2.1 Computer Vision and Video Analysis	16](#2.2.1-computer-vision-and-video-analysis)  
[2.2.2 Machine Learning in Sports Analytics	16](#2.2.2-machine-learning-in-sports-analytics)  
[2.2.3 Speech Recognition and Audio Analysis	17](#2.2.3-speech-recognition-and-audio-analysis)  
[2.2.4 Multimodal Integration	17](#2.2.4-multimodal-integration)

[**2.3 Related Work	17**](#2.3-related-work)  
[2.3.1 Multimodal Soccer Video Analysis	17](#2.3.1-multimodal-soccer-video-analysis)

[**2.4 Conclusion	19**](#2.4-conclusion)

[***Chapter 3:  Requirements Analysis and Specification	20***](#chapter-3:- requirements-analysis-and-specification)

[**3.1 Requirement Elicitation Method	20**](#3.1-requirement-elicitation-method)

[**3.2 User Requirements	21**](#3.2-user-requirements)  
[3.2.1 Functional Requirements	21](#3.2.1-functional-requirements)  
[FR1. Centralized Squad Management System	21](#fr1.-centralized-squad-management-system)  
[FR2. Video Upload and Automated Analysis Pipeline	21](#fr2.-video-upload-and-automated-analysis-pipeline)  
[FR3. Tactical Intelligence and Feedback Generation	22](#fr3.-tactical-intelligence-and-feedback-generation)  
[FR4. Interactive AI Coaching Assistant	22](#fr4.-interactive-ai-coaching-assistant)  
[FR5. Autonomous Opponent Analysis Agent	23](#fr5.-autonomous-opponent-analysis-agent)  
[FR6. AI-Powered Talent Scouting Agent	23](#fr6.-ai-powered-talent-scouting-agent)

[**3.2.2 Non-Functional Requirements	25**](#3.2.2-non-functional-requirements)  
[NFR1. Performance Efficiency	25](#nfr1.-performance-efficiency)  
[NFR2. Usability	25](#nfr2.-usability)  
[NFR3. Scalability	25](#nfr3.-scalability)

[**3.3 System Requirements	26**](#3.3-system-requirements)  
[System Actors	26](#system-actors)  
[List of Use Cases	27](#list-of-use-cases)  
[3.3.1 Detailed Use Case Descriptions	27](#3.3.1-detailed-use-case-descriptions)  
[UC1 – Manage Squad Players	27](#uc1-–-manage-squad-players)  
[UC2 – Upload Match Video	27](#uc2-–-upload-match-video)  
[UC3 – Generate & View Tactical Intelligence	28](#uc3-–-generate-&-view-tactical-intelligence)  
[UC4 – Interact With AI Coach	28](#uc4-–-interact-with-ai-coach)  
[UC5 – Request Opponent Analysis Report	28](#uc5-–-request-opponent-analysis-report)  
[UC6 – Request Talent Scout Recommendations	29](#uc6-–-request-talent-scout-recommendations)  
[UC7 – View Coaching Dashboard and Match History	29](#uc7-–-view-coaching-dashboard-and-match-history)  
[3.3.2 Non-Functional Requirements	29](#3.3.2-non-functional-requirements)

[**3.4 High-Level System Architecture	30**](#3.4-high-level-system-architecture)

[**3.5 project timeline	32**](#3.5-project-timeline)

[**3.6 Conclusion	32**](#3.6-conclusion)

[***References	33***](#references)

# 

# **List of Figures** {#list-of-figures}

[Figure 1Project Time Line	9](#figure-1project-time-line)  
[Figure 2 Use Case Diagram	21](#heading=h.yyd7aj7fev9c)  
[Figure 3 High level System Architecture	25](#heading=h.e0kylwlibqb1)  
[Figure 4 Project Plan	26](#figure-4-project-plan)

# 

List of Tables

#  {#heading}

[Table 1 Team Members	10](#table-1-team-members)  
[Table 2 A comparison of related works in multimodal soccer video analysis	15](#table-2-a-comparison-of-related-works-in-multimodal-soccer-video-analysis)

# **List of Abbreviations** {#list-of-abbreviations}

| Abbreviation | Definition |
| :---- | :---- |
| **AI** | Artificial Intelligence |
| **API** | Application Programming Interface |
| **ASPERA** | Action SPotting thrEe-modal Recognition Architecture |
| **ASR** | Automatic Speech Recognition |
| **CNN** | Convolutional Neural Network |
| **CV** | Computer Vision |
| **FR** | Functional Requirement |
| **GP** | Graduation Project |
| **HTTPS** | Hypertext Transfer Protocol Secure |
| **KPI** | Key Performance Indicator |
| **ML** | Machine Learning |
| **NFR** | Non-Functional Requirement |
| **UC** | Use Case |
| **UI** | User Interface |
| **YOLO** | You Only Look Once (Object Detection Algorithm) |

# **Chapter 1: Introduction** {#chapter-1:-introduction}

## **1.1 Overview**  {#1.1-overview}

Performance coaching in football has evolved rapidly, relying heavily on technology to boost player development and tactical intelligence. However, a significant disparity persists: high-quality, personalized coaching is largely reserved for professional and elite-level environments, with limited access at amateur and grassroots levels. While professional teams benefit from specialized performance analysis units staffed by expert analysts and data scientists, most players are restricted to manual video reviews or basic game statistics. These numbers might indicate *what* happened—such as possession percentages or shot counts—but they rarely explain *why* it happened or *how* to improve. This creates a clear need for an intelligent system capable of analyzing gameplay to provide the "why" behind the performance.   
Previous research in sports analytics has made great strides using computer vision and multimodal learning. Innovative frameworks have successfully combined video, audio, and commentary data to spot key events and create highlights. However, while these tools are excellent at describing the action in professional broadcast footage, they often lack the personal touch. They tend to remain descriptive rather than diagnostic, stopping short of offering the specific, individualized recommendations that a player needs to grow.   
This project aims to bridge the critical gap between purely descriptive match statistics and actionable, personalized coaching. By applying computer vision, machine learning, and audio-visual integration, we are developing a system designed to analyze gameplay footage deeply. The goal is to move beyond simple tracking and instead extract tactical patterns, identify player weaknesses, and generate coaching feedback that is both contextual and actionable. Unlike existing methods that focus on broadcasting or broad data, this system focuses on the individual, offering interactive feedback suitable for players of all skill levels.  
This chapter lays the groundwork for the project. It starts by defining the core problem and the evidence behind these coaching challenges, followed by the specific aims and objectives established to resolve them. We also outline the team’s qualifications to demonstrate our capability to deliver this solution. Finally, the chapter concludes with a summary that highlights the project's significance and sets the stage for the literature review in the following chapter. 

## **1.2 Problem Definition** {#1.2-problem-definition}

The core technical challenge in this project is the absence of an intelligent system capable of automatically analyzing gameplay videos to identify tactical patterns, individual player weaknesses, and improvement opportunities using computer vision and machine learning. Current tools mainly focus on descriptive statistics—like possession, shots, or passes—without generating diagnostic insights or personalized feedback. This creates a research challenge: developing an AI model that can extract, interpret, and evaluate player actions contextually, transforming unstructured gameplay footage into structured, actionable performance insights.  
To better understand the scope of this problem, we identified several key challenges in the current landscape:

* **Coaching access is expensive and uneven.** High-quality one-to-one coaching typically costs from about $40 to $120 per hour, and premium or elite coaches often charge $90 to $100+ per hour. This price point effectively prices out many amateurs and students, making professional feedback a luxury.   
* **Manual video review is slow and hard to scale.** Analyzing match footage requires hours of manual tagging and review. In research settings, reviewers have reported a median of roughly 2.5 hours of analysis for every single hour of video, which is impractical for busy coaches and teams to maintain.   
* **Basic statistics miss tactical context.** Traditional metrics such as total shots, corners, or raw possession numbers often correlate poorly with actual decision quality. They fail to account for situational context, such as team shape, pressing triggers, and specific player roles.   
* **Feedback is descriptive, not prescriptive.** Conventional tools tell players *what* happened, but they rarely translate those patterns into step-by-step, role-specific drills or micro-adjustments in positioning and decision-making that a player can practice immediately.  
* **Grassroots implementation is cumbersome.** Amateur clubs often report cost, logistics, and setup time as major barriers to adopting video analytics across multiple matches and venues. This difficulty limits the ability to create consistent feedback loops for players. 

## **1.3 Aims and Objectives** {#1.3-aims-and-objectives}

The primary aim of this project is to **empower football coaches with an AI-driven tactical intelligence platform** that democratizes access to elite-level analytics, opponent analysis, and talent scouting capabilities. By integrating lightweight computer vision, machine learning models, and autonomous AI agents, the system transforms raw match footage and fragmented data into a unified coaching command center that delivers actionable tactical insights, opponent intelligence, and data-driven player recruitment recommendations.  
Unlike existing solutions that passively describe events for spectators, this platform is purpose-built for **active coaching decision-making** bridging the gap between manual video review, disconnected statistics, and the strategic intelligence required to compete at higher levels.

To achieve this, we have defined the following technical and operational objectives:

#### **1\. Intelligent Match Analysis & Tactical Feedback System**

**Objective:**  
To develop an integrated platform that combines lightweight computer vision, squad management, and natural language AI to transform match footage into actionable coaching insights.  
**Key Components:**

* **Centralized Squad Intelligence Dashboard**: A comprehensive system that aggregates player performance data, tactical profiles, and historical analytics into a unified interface, allowing coaches to visualize squad-wide trends and identify tactical patterns  
* **Lightweight Video Analysis Pipeline**: An optimized CV module utilizing efficient object detection algorithms (e.g., YOLOv8) to extract tactical events while minimizing computational overhead, making the system accessible on standard hardware  
* **AI-Powered Tactical Feedback Engine**: Automated generation of coach-oriented tactical observation notes by linking visual analysis with squad statistics (e.g., "Team shape collapsed when the left-back pushed forward—recommend adjusting defensive trigger points")  
* **Conversational AI Coach Interface**: A natural language processing system that allows coaches to query match data interactively, receiving context-aware answers synthesized from video analysis and performance metrics through a chat-based interface

**Engineering Challenge:**  
Balancing analytical depth with processing efficiency—delivering professional-grade insights while maintaining fast processing times on consumer hardware, and designing a data model that presents complex tactical information in an immediately actionable format.  
---

#### **2\. Multi-Agent Intelligence System for Strategic Decision Support**

**Objective:**  
To architect and deploy autonomous AI agents that extend coaching capabilities beyond post-match review by providing proactive opponent analysis and data-driven talent scouting.  
**Key Components:**

* **Opponent Analysis Agent**: An AI agent capable of autonomously processing opponent match data (footage, statistics, formation patterns) to generate pre-match tactical reports that identify exploitable weaknesses, predictable patterns, and recommended counter-tactics tailored to the opponent's style  
* **Talent Scout Agent**: An autonomous scouting system that searches player databases and match repositories to identify recruitment candidates matching the club's tactical profile and budget constraints, utilizing machine learning classification models to rank players based on positional fit and statistical compatibility  
* **Agent Integration Framework**: A unified architecture that allows both agents to communicate findings to the central dashboard and AI coach, ensuring seamless access to opponent intelligence and scouting recommendations during tactical planning

**Engineering Challenge:**  
Designing agents with sufficient tactical domain knowledge to avoid generic recommendations—requiring integration of formation databases, tactical ontologies, and player attribute taxonomies—while ensuring agent outputs are verifiable and grounded in actual data rather than speculative analysis.  
---

#### **3\. Predictive Analytics & User-Centric Validation**

**Objective:**  
To implement machine learning models for predictive tactical insights and validate the entire system's effectiveness through rigorous testing with real coaching workflows.  
**Key Components:**

* **Predictive ML Models**: Lightweight regression and classification models to forecast match outcomes, categorize tactical scenarios (e.g., "high-intensity press," "defensive block"), and detect performance anomalies (e.g., unusual fatigue indicators), supplementing computer vision with pattern recognition that identifies hidden trends  
* **Coach-Centric UX Design**: A mobile-responsive interface optimized for workflow efficiency, presenting complex analytics through annotated video overlays, heatmaps, and visual tactical concepts rather than raw numerical tables, supporting rapid decision-making during match preparation  
* **Validation & Performance Benchmarking**: Controlled pilot studies measuring system accuracy (CV precision vs. manual annotations), usability (coaching workflow time reduction), and tactical value (expert evaluation of agent recommendations), with iterative refinement based on real coaching staff feedback

**Success Metrics:**

* Video processing time reduced by at least 50% compared to manual review  
* Coach satisfaction score (usability survey) exceeding 4.0/5.0  
* At least 70% of agent recommendations rated as "tactically sound" by professional coaches

**Engineering Challenge:**  
Training accurate predictive models with limited data from amateur clubs—requiring transfer learning strategies and data augmentation—while ensuring the user experience remains intuitive for non-technical coaches under time pressure.

## **1.4 Project Timeline** {#1.4-project-timeline}

![][image1]  
*Figure 1Project Time Line*

The project timeline, illustrated in **Figure 1**, outlines the structured execution plan for the first semester of 2025 (September through December). The schedule is divided into four sequential and overlapping phases:

* **Project Initiation & Proposal (September):** This initial phase focuses on defining the project scope and submitting the formal proposal for faculty review and approval.  
* **Literature Review & Research (October):** Following initiation, the focus shifts to analyzing related work and state-of-the-art technologies to establish a theoretical foundation.  
* **Requirements Analysis & Specification (November – December):** The latter half of the semester is dedicated to eliciting user needs, defining functional specifications, and modeling the system architecture.  
* **Documentation (September – December):** As a continuous parallel activity, documentation runs throughout the entire lifecycle to ensure that all research findings, technical decisions, and specifications are rigorously recorded for the final report.

1.5 Team Qualifications

*Table 1 Team Members*

| Name | Focus & Specialization | Skills & Tech | Projects & Experience | Distinctive Strengths |
| :---- | :---- | :---- | :---- | :---- |
| Zeyad bin Nazir | Mobile App Dev & UI/UX | Flutter, HTML, CSS, Clean Architecture | TourKSA (Tourist Guide), Wasel App (Hackathon Winner) | Leadership (Student Activities), Intuitive UX Design, Team Coordination. |
| Marwan Abdullah Ali | Data Science & ML | Python (Pandas, Scikit-learn), Flutter, Dart | Medical Cost Prediction Model, AI-powered Tourism App | Integrating AI into applications, Algorithmic Thinking, Modeling & Analysis. |
| Khalid AldawisH | Project Leader, AI and Data Engineer. | Python, FastAPI, ML, AI Agents, Data Warehouse, Backend  | Salla AI Agent, Demand Forecasting Agent, Market Trading  | System Architecture, Connecting Backend with AI Logic, Technical Documentation. |
| Khaled AL-Ghilan | Full-Stack Web Development | React, Node.js, Next.js, Appwrite, Flutter | High-performance Web Interfaces, Robust Backend Services | JavaScript Ecosystem Mastery, Scalable App Building, Web & Mobile Versatility. |

The development team comprises four specialists whose combined expertise covers the full technical stack required for the AI Coaching System. **Khalid Aldawish** serves as the Project Leader and AI Engineer, bringing critical experience in backend architecture, **Computer Vision workflows**, and AI agent integration using FastAPI and Python. Complementing this, **Marwan Abdullah Ali** leads the Data Science and Machine Learning efforts, utilizing Python and Scikit-learn to design the algorithmic models and **video processing logic** central to the project's analytical capabilities.  
To ensure a robust user experience, **Khaled Al-Ghilan** provides full-stack expertise with React and Node.js, focusing on scalable web interfaces and backend services. **Zeyad Bin Nazir** completes the team with a specialization in Mobile App Development and UI/UX design, leveraging Flutter to ensure the final product is intuitive and accessible. Together, this multidisciplinary team possesses the necessary balance of system architecture, **visual data processing**, and frontend design skills to successfully deliver the proposed solution.

## 

## **1.6 Conclusions** {#1.6-conclusions}

This chapter established the foundation of the project by identifying a critical gap in the current landscape of football coaching technology. Existing tools provide descriptive match statistics or expensive manual video analysis, yet they fail to deliver the **integrated tactical intelligence** that coaches need to make strategic decisions efficiently. Coaching staff at amateur and semi-professional levels face significant barriers: high costs for specialized analysts, time-consuming manual video review (averaging 2.5 hours of analysis per hour of footage), and fragmented data sources that fail to connect player performance with opponent analysis and talent recruitment.  
Several commercial and academic systems attempt to analyze match data, yet they primarily focus on broadcast summarization for spectators or require professional-grade infrastructure beyond the reach of grassroots clubs. More critically, **no existing platform unifies squad management, tactical video analysis, opponent intelligence, and AI-powered scouting** into a single coaching workflow. This fragmentation forces coaches to manually synthesize insights across disconnected tools, creating inefficiencies that limit their ability to compete strategically.  
To address this gap, the proposed project will develop an **AI-driven coaching platform** that applies lightweight computer vision, machine learning, and autonomous agent architectures to transform raw match footage and player data into a unified command center for tactical decision-making. Unlike existing methods that serve passive observation, this system emphasizes **active coaching support** through three core capabilities:

1. **Intelligent match analysis** that generates tactical feedback by linking video events with squad statistics  
2. **Multi-agent intelligence** providing autonomous opponent analysis and data-driven talent scouting  
3. **Conversational AI coach** enabling natural language queries across all system data

By shifting from broadcast-oriented tools to a **coach-centric platform**, this project aims to democratize access to elite-level tactical intelligence, enabling coaches at all levels to make data-informed decisions that were previously exclusive to professional clubs with dedicated analytics departments.  
The next chapter, **Chapter 2 – Literature Review**, will present a detailed examination of the technical foundations underpinning this solution—including computer vision for sports video analysis, machine learning for tactical prediction, autonomous agent architectures for strategic intelligence, and multimodal integration techniques—while analyzing related research to position this project within the broader academic and industry context.

# **Chapter 2: Literature Review Chapter** {#chapter-2:-literature-review-chapter}

## **2.1 Introduction**  {#2.1-introduction}

The scientific basis of the proposed solution becomes evident through a detailed analysis of existing research which the chapter presents. Chapter 1: Introduction explores the rising demand for customized sports analysis feedback through user-generated content evaluation, which serves as the foundation for this research study.   
The chapter serves two main functions, which help readers with computing expertise understand the technical foundation of this project and evaluate current state-of-the-art solutions to establish the research gap that this study will fill. 

## **2.2 Background** {#2.2-background}

### **2.2.1 Computer Vision and Video Analysis** {#2.2.1-computer-vision-and-video-analysis}

The cornerstone of modern sports analytics is **Computer Vision (CV)**, which allows a machine to "see" and parse visual data from video frames.

* **Object Detection:** We rely on algorithms like **YOLOv8** (You Only Look Once), which has become the industry standard for real-time detection. It is capable of identifying players, the ball, and referees even in challenging environments where lighting varies or the camera moves rapidly.  
* **Object Tracking:** Detection is only the first step; we also need to maintain identity over time. Systems like **ByteTrack** allow us to track player trajectories across sequential frames. This is crucial for tactical analysis, as it lets the system understand movement flow rather than just static positions.  
* **Action Recognition:** Finally, to understand *what* a player is doing, we utilize Deep Learning models that combine **Convolutional Neural Networks (CNNs)** with **Transformers**. This architecture allows the system to recognize specific actions (like a tackle or a shot) by analyzing spatial-temporal features—essentially treating the game as a sequence of meaningful events rather than just pixels.

### **2.2.2 Machine Learning in Sports Analytics** {#2.2.2-machine-learning-in-sports-analytics}

If Computer Vision is the eyes, **Machine Learning (ML)** is the brain. ML pipelines are responsible for transforming raw coordinate data extracted from video into meaningful tactical insights.

Rather than just logging where a player is, advanced neural architectures can analyze spatial relationships to evaluate technical skills and tactical decisions. For example, regression analysis can differentiate between a "successful pass" and a "missed chance" by looking at the context of the play. By extracting these spatial-temporal features, ML models enable the system to move from simple observation to diagnostic feedback, opening the door for automated, personalized coaching recommendations.

### **2.2.3 Speech Recognition and Audio Analysis** {#2.2.3-speech-recognition-and-audio-analysis}

Visual data often has gaps—players get blocked from view, or actions happen off-screen. This is where **Audio Analysis** becomes a critical redundant system.

* **Automatic Speech Recognition (ASR):** Modern ASR systems, such as OpenAI's **Whisper** or Google Speech-to-Text, have achieved high accuracy in transcribing commentary. By parsing this text, a system can identify key context (e.g., a commentator shouting "Goal\!" or discussing a specific player).  
* **Environmental Audio:** Beyond speech, the audio signal itself contains valuable cues. The distinct sound of a referee's whistle, the roar of a crowd, or the thud of the ball can be used to pinpoint high-intensity events.

### **2.2.4 Multimodal Integration** {#2.2.4-multimodal-integration}

The cutting edge of sports analytics lies in **Multimodal Learning**—the fusion of video, audio, and text. Recent frameworks, such as **ASPERA** and the **SoccerNet-Echoes** dataset, have demonstrated that systems perform significantly better when they "listen" as well as "watch." By combining visual features with audio transcripts, these systems achieve higher accuracy in event spotting and highlight generation, providing a more robust understanding of the match than any single modality could achieve alone.

## **2.3 Related Work** {#2.3-related-work}

In this section, we examine the current landscape of multimodal video analysis. The research in this field has shifted significantly in recent years, moving away from simple, single-stream visual models toward complex systems that integrate video, audio, and textual commentary to "understand" a football match.  
Our review focuses on recent frameworks that attempt to capture the context, emotion, and tactical meaning of in-game events. While these systems represent the state-of-the-art, our analysis highlights a critical limitation: they are almost exclusively designed for professional broadcasting and passive viewing, rather than active, personalized coaching.

### **2.3.1 Multimodal Soccer Video Analysis** {#2.3.1-multimodal-soccer-video-analysis}

The integration of multiple data sources—sight, sound, and language—has proven to be a game-changer for automated analysis.

**ASPERA (2025)** represents a major step forward in this domain. This framework introduced a "three-modal" architecture that simultaneously processes video feeds, audio signals, and commentary text. The researchers demonstrated that by processing these three streams jointly, the system could recognize events with significantly higher precision than visual-only models. However, ASPERA is heavily reliant on the high production value of professional broadcasts. It struggles with the chaotic nature of raw gameplay footage where visual obstructions are common and professional commentary is absent. \[6\]

Building on this, **SoccerNet-Echoes (2024)** expanded the possibilities of audio-visual fusion. This study developed a massive dataset combining video with transcripts generated by Automatic Speech Recognition (ASR). The project proved that "listening" to the game allows AI to better summarize matches and spot key events that might be visually ambiguous. Yet, like ASPERA, its reliance on broadcast-quality footage makes it difficult to adapt for grassroots players or amateur recordings, which rarely have clean audio or professional commentary tracks. \[7\]

Taking a different approach, **SoccerChat (2023)** explored the potential of conversational AI. By fusing visual data with text, the researchers trained agents capable of reasoning about match events and even replicating referee decision-making through dialogue. While this introduced a fascinating level of interactivity, the system’s primary focus was on replicating the *rules* of the game and facilitating conversation, rather than analyzing player performance or offering tactical coaching advice. \[8\]

###  

2.3.2 Comparison Table

*![صورة تحتوي على نص, لقطة شاشة, الخط, رقمقد يكون المحتوى الذي تم إنشاؤه بواسطة الذكاء الاصطناعي غير صحيح.][image2]*

*Table 2 A comparison of related works in multimodal soccer video analysis*

As summarized in Table 1, a distinct trend emerges from the literature. While frameworks like **ASPERA** and **SoccerNet-Echoes** have advanced the field by integrating video, audio, and text, they share a fundamental constraint: they are engineered for the broadcast booth, not the training ground. Because they rely on high-production features—such as professional commentary and steady camera angles—they excel at **describing** what happened for a spectator but fail to explain **how** a player can improve.  
Even interactive models like **SoccerChat**, while innovative, prioritize conversational rule interpretation over actual performance analysis. Consequently, there is no existing solution that can take raw, amateur footage and generate the kind of diagnostic, prescriptive feedback a coach would provide. This project aims to fill that specific void, moving the technology from passive observation to active, personalized coaching.

## **2.4 Conclusion**  {#2.4-conclusion}

This chapter has established the theoretical foundation for our proposed system by exploring the core technologies behind multimodal sports analysis: Computer Vision, Machine Learning, and Audio-Visual Integration.  
Our review of the literature confirms that while audio-visual fusion has immense potential, current research is heavily skewed toward professional use cases. State-of-the-art systems primarily focus on processing high-quality broadcast footage to classify events or generate highlight reels for spectators. They effectively ignore the needs of the individual player, failing to provide the kind of personalized, context-aware feedback that is essential for improvement.  
To bridge this gap, this project aims to develop a unified framework that merges player detection, action recognition, and audio analysis into a single coaching tool. By moving beyond simple event spotting, our system seeks to "understand" player performance in raw gameplay videos, setting a new benchmark for automated, accessible coaching.  
With the technical background and research gap now clearly defined, the following chapter, **Chapter 3: System Analysis**, will detail the Requirements Analysis and Specification, outlining the specific functional and non-functional criteria necessary to build this novel system.

# **Chapter 3:  Requirements Analysis and Specification**  {#chapter-3:- requirements-analysis-and-specification}

Having established the theoretical foundations and identified the research gap in the previous chapter, Chapter 3 shifts focus to the practical realization of the proposed solution. This chapter serves as the engineering blueprint for the **AI-Powered Coaching Platform**, translating the identified **coaching needs** into formal technical specifications.  
The chapter begins by detailing the Requirement Elicitation Method, explaining the collaborative brainstorming process used to define the system's scope and **coaching workflow**. We then categorize the system's specifications into **Functional Requirements**, which define the core capabilities—such as automated video analysis, **multi-agent intelligence** (opponent analysis and talent scouting), squad management dashboards, and the interactive AI coach—and **Non-Functional Requirements**, which establish the quality constraints regarding performance, security, and usability. Finally, the chapter presents the **System Requirements** through detailed Use Case descriptions and modeling, providing a structured framework that guides the subsequent design and implementation phases.

## **3.1 Requirement Elicitation Method** {#3.1-requirement-elicitation-method}

To define the scope and capabilities of the proposed system, the development team utilized **structured brainstorming sessions** as the primary requirement elicitation technique. This collaborative approach allowed us to explore the problem space deeply, identifying not just technical constraints but also the specific "pain points" that users face in the current landscape of sports analysis.

The sessions were designed to deconstruct the entire user journey—from the moment a match is recorded to the point where a player seeks advice on how to improve. Key areas of discussion included:

* **Current Training Workflows:** Analyzing how amateur players currently attempt to improve their performance and identifying where these existing methods fail (e.g., the subjectivity of self-review).  
* **Friction Points in Manual Analysis:** Pinpointing the specific bottlenecks in manual video review, such as the time required to tag events and the difficulty of spotting off-ball tactical errors.  
* **AI Coach Expectations:** Defining the "ideal" interactions between a user and an automated system—specifically, what kind of feedback feels "human" and actionable versus robotic and purely statistical.  
* **The Player Lifecycle:** Mapping the user's experience before, during, and after gameplay to ensure the system supports the entire improvement loop.

This elicitation process resulted in a unified vision of the user’s goals, which directly informed the functional and non-functional requirements detailed in the following sections.

## **3.2 User Requirements** {#3.2-user-requirements}

## 

### **3.2.1 Functional Requirements** {#3.2.1-functional-requirements}

The functional requirements describe the specific behaviors and services the system must provide. These are organized by the logical flow of the application, from user onboarding to advanced tactical analysis.

### **FR1. Centralized Squad Management System** {#fr1.-centralized-squad-management-system}

To enable effective coaching decisions, the platform must provide a unified interface for managing all squad-related data. This centralization is critical for coaches to maintain visibility over player performance trends, tactical profiles, and development trajectories.  
**Requirements:**

* The system shall allow coaches to create and manage comprehensive player profiles, including positional data, technical attributes, tactical strengths, and weaknesses  
* The system must aggregate historical performance statistics across multiple matches, presenting trends in key metrics such as passing accuracy, defensive actions, and positioning discipline  
* The system shall provide role-based player categorization (e.g., "High-Pressing Forward," "Ball-Playing Defender") to support tactical planning and formation decisions  
* The system must enable coaches to add custom notes and observations to individual player profiles for long-term development tracking

**Coaching Value:**  
This requirement eliminates fragmented spreadsheets and manual record-keeping, providing coaches with instant access to squad intelligence that informs selection decisions and tactical adjustments.

### **FR2. Video Upload and Automated Analysis Pipeline** {#fr2.-video-upload-and-automated-analysis-pipeline}

The platform must simplify the process of converting raw match footage into structured tactical data. By automating video processing, the system reduces the manual burden on coaches while ensuring consistent analytical output.  
**Requirements:**

* The system shall provide an intuitive interface for coaches to upload match recordings in common video formats (MP4, MOV, AVI)  
* The system must automatically trigger a lightweight computer vision pipeline upon upload, utilizing optimized object detection algorithms to identify players, ball trajectories, and spatial formations  
* The system shall process video asynchronously in the background, allowing coaches to continue other tasks while analysis runs  
* The system must provide upload progress indicators and notify coaches upon completion of video processing

**Coaching Value:**  
Coaches can delegate the time-consuming task of video tagging to the system, reclaiming hours previously spent on manual review and enabling focus on tactical interpretation rather than data extraction.

### **FR3. Tactical Intelligence and Feedback Generation** {#fr3.-tactical-intelligence-and-feedback-generation}

Beyond extracting raw data from video, the system must interpret tactical events and generate coach-oriented insights that explain performance patterns and suggest corrective actions.  
**Requirements:**

* The system shall analyze processed video data to identify tactical events, including defensive shape errors, attacking pattern breakdowns, pressing trigger failures, and set-piece vulnerabilities  
* The system must correlate video observations with player statistics to provide contextual explanations (e.g., "Defensive line dropped 8 meters deeper in the second half, coinciding with a 15% decrease in ball recovery rate")  
* The system shall generate tactical observation notes in natural language, presenting findings in a format that mimics human coach analysis rather than raw statistical output  
* The system must allow coaches to review tagged tactical events alongside the original video footage, enabling verification of AI-generated insights

**Coaching Value:**  
This requirement transforms the system from a descriptive tool into a diagnostic assistant, helping coaches understand not just *what* happened, but *why* it happened and *how* to address it.

### **FR4. Interactive AI Coaching Assistant** {#fr4.-interactive-ai-coaching-assistant}

Static reports can be overwhelming; this requirement introduces a conversational layer that allows coaches to explore match data interactively through natural language queries.  
**Requirements:**

* The system shall provide a chat-based interface where coaches can ask questions about player performance, tactical patterns, and strategic recommendations  
* The AI assistant must synthesize information from multiple data sources (video analysis, squad statistics, opponent intelligence) to provide comprehensive answers  
* The system shall maintain conversational context across multiple exchanges, allowing coaches to refine queries without re-explaining prior context (e.g., "Show me defensive errors" → "Now filter by the last 3 matches")  
* The system must ground all responses in actual match data, citing specific examples and statistics to ensure verifiability and trust

**Coaching Value:**  
Coaches can rapidly explore complex questions ("How does our pressing intensity change when playing against possession-based teams?") without navigating multiple dashboards or running manual queries.

### **FR5. Autonomous Opponent Analysis Agent** {#fr5.-autonomous-opponent-analysis-agent}

Preparation is half the battle; this requirement provides coaches with proactive intelligence on upcoming opponents, automating the scouting process that traditionally requires hours of manual video review.  
**Requirements:**

* The system shall deploy an AI agent capable of processing opponent match footage and publicly available performance data  
* The agent must identify opponent tactical patterns, including preferred formations, attacking build-up sequences, defensive vulnerabilities, and set-piece routines  
* The system shall generate pre-match tactical reports highlighting exploitable weaknesses and recommended counter-strategies tailored to the opponent's style  
* The agent must rank identified patterns by frequency and success rate, prioritizing insights most likely to impact match outcomes

**Coaching Value:**  
Coaches gain access to structured opponent intelligence without dedicating significant time to manual analysis, enabling data-driven tactical preparation even with limited staff resources.

### **FR6. AI-Powered Talent Scouting Agent** {#fr6.-ai-powered-talent-scouting-agent}

Recruitment is a continuous challenge for clubs; this requirement provides coaches with an automated assistant that searches for player candidates matching the team's tactical profile and budget constraints.  
**Requirements:**

* The system shall provide an autonomous scouting agent that searches player databases and match footage repositories based on coach-defined criteria (position, playing style, age, estimated market value)  
* The agent must utilize machine learning classification models to rank candidates based on statistical compatibility with the team's playing style and tactical requirements  
* The system shall generate candidate comparison reports showing how prospective players align with current squad profiles and where they would add tactical value  
* The agent must explain its recommendations, providing transparency into the ranking logic (e.g., "Player X offers similar passing range but with 20% higher defensive work rate")

**Coaching Value:**  
Coaches can identify recruitment targets systematically rather than relying solely on network referrals or manual observation, expanding the talent pool and improving the quality of signing decisions.

## **3.2.2 Non-Functional Requirements** {#3.2.2-non-functional-requirements}

While functional requirements define what the system does, non-functional requirements (NFRs) define how well it must perform. These constraints ensure the platform is efficient, user-friendly, and architecturally sound.  
---

### **NFR1. Performance Efficiency** {#nfr1.-performance-efficiency}

The system must process computationally intensive tasks within practical timeframes to support coaching workflows.  
**Requirements:**

* **Video Processing**: The analysis pipeline must process a 10-minute match clip within **3-5 minutes** on standard hardware  
* **Dashboard Responsiveness**: Performance visualizations and reports must render within **2-3 seconds** of navigation  
* **AI Coach Latency**: The conversational assistant must generate responses within **5-10 seconds** to maintain natural interaction flow  
* **Agent Reports**: Opponent analysis and scouting agents should produce reports within **10-15 minutes**

---

### **NFR2. Usability** {#nfr2.-usability}

The interface must be intuitive for coaches with limited technical experience, presenting complex data in accessible formats.  
**Requirements:**

* **Minimal Training**: Core features should be navigable with less than **15 minutes** of onboarding  
* **Clear Visualizations**: Tactical displays (heatmaps, movement vectors) must use intuitive color schemes with clear legends  
* **Natural Language**: The AI coach shall accept conversational queries without rigid command syntax  
* **Actionable Feedback**: System messages must use coach-friendly language, avoiding technical jargon

---

### **NFR3. Scalability** {#nfr3.-scalability}

The architecture must support future expansion through modular design and extensible components.  
**Requirements:**

* **Modular Design**: System components (CV pipeline, agents, frontend) shall be loosely coupled with well-defined APIs  
* **Extensible Data Model**: Database schema should accommodate new metrics and attributes without major refactoring  
* **Agent Framework**: The multi-agent system shall support adding new specialized agents without core platform modifications  
* **Clean Architecture**: Code shall follow established patterns with clear separation of concerns

## **3.3 System Requirements** {#3.3-system-requirements}

This section translates the high-level coaching needs identified in the previous section into formal system requirements. These specifications serve as the blueprint for the system's architecture and implementation. Functional requirements are modeled through structured Use Case descriptions, detailing the interactions between the coach and the system, as illustrated in Figure 2\. Furthermore, non-functional requirements are expanded to define the specific quality attributes such as performance, usability, and scalability that the system must satisfy.

*Figure 2 Use Case Diagram*

![][image3]

---

### **System Actors** {#system-actors}

* **Primary Actor: The Coach** – The coaching staff member utilizing the platform to analyze matches, manage squad intelligence, and receive tactical recommendations  
* **System: AI-Powered Coaching Platform** – The automated platform responsible for processing video, generating tactical analytics, orchestrating AI agents, and providing strategic intelligence

---

### **List of Use Cases** {#list-of-use-cases}

The core functionality of the system is encapsulated in the following use cases:

* **UC1**: Manage Squad Players  
* **UC2**: Upload Match Video  
* **UC3**: Generate and View Tactical Intelligence  
* **UC4**: Interact With AI Coach (Chat)  
* **UC5**: Request Opponent Analysis Report  
* **UC6**: Request Talent Scout Recommendations  
* **UC7**: View Coaching Dashboard and Match History

---

### **3.3.1 Detailed Use Case Descriptions** {#3.3.1-detailed-use-case-descriptions}

### **UC1 – Manage Squad Players** {#uc1-–-manage-squad-players}

* **Actor**: Coach  
* **Pre-condition**: The coach has successfully authenticated and has access to the platform  
* **Main Flow**:   
  1. The coach navigates to the Squad Management interface  
  2. The coach creates or updates player profiles, including positional data, tactical attributes, strengths, and development notes  
  3. The system validates and stores the player metadata  
  4. The system displays the updated squad roster with aggregated statistics  
* **Post-condition**: Player profiles are established and linked to all subsequent tactical analysis and performance tracking

---

### **UC2 – Upload Match Video** {#uc2-–-upload-match-video}

* **Actor**: Coach  
* **Pre-condition**: The coach has access to the platform and squad profiles exist  
* **Main Flow**:   
  1. The coach selects a match video file from their local device for upload  
  2. The system validates the file format and integrity  
  3. The system stores the video in the cloud storage  
  4. The system automatically triggers the asynchronous computer vision analysis pipeline  
* **Alternate Flow (2a)**: If the file format is unsupported, the system terminates the upload and displays an error message  
* **Post-condition**: The raw video is stored and queued for tactical analysis processing

---

### **UC3 – Generate & View Tactical Intelligence** {#uc3-–-generate-&-view-tactical-intelligence}

* **Actor**: Coach  
* **Pre-condition**: A video has been successfully uploaded and the processing pipeline is complete  
* **Main Flow**:   
  1. The system executes object detection and tracking algorithms on the footage  
  2. The system identifies tactical events (defensive errors, pressing triggers, formation breakdowns) and correlates them with squad statistics  
  3. The system generates tactical observation notes in natural language  
  4. The coach navigates to the Tactical Intelligence view  
  5. The system renders the analysis with annotated video clips, heatmaps, and tactical recommendations  
* **Post-condition**: Structured tactical intelligence is available for review and can be queried via the AI coach interface

---

### **UC4 – Interact With AI Coach** {#uc4-–-interact-with-ai-coach}

* **Actor**: Coach  
* **Pre-condition**: At least one match analysis has been completed to provide context  
* **Main Flow**:   
  1. The coach initiates a chat session via the AI coach interface  
  2. The coach submits a natural language query (e.g., "What are our main defensive weaknesses against possession-based teams?")  
  3. The system queries the tactical intelligence database, squad statistics, and agent reports to formulate a response  
  4. The system delivers evidence-based tactical advice with references to specific match moments  
* **Post-condition**: The coach receives actionable tactical guidance synthesized from multiple data sources

---

### **UC5 – Request Opponent Analysis Report** {#uc5-–-request-opponent-analysis-report}

* **Actor**: Coach  
* **Pre-condition**: The coach has access to the platform and opponent match data is available (uploaded or linked)  
* **Main Flow**:   
  1. The coach requests opponent analysis by uploading opponent footage or selecting from a database  
  2. The system activates the Opponent Analysis Agent  
  3. The agent processes the opponent data to identify tactical patterns, formations, and vulnerabilities  
  4. The system generates a pre-match tactical report with recommended counter-strategies  
  5. The coach reviews the report via the dashboard  
* **Post-condition**: The coach receives structured opponent intelligence to inform match preparation

---

### **UC6 – Request Talent Scout Recommendations** {#uc6-–-request-talent-scout-recommendations}

* **Actor**: Coach  
* **Pre-condition**: Squad profiles exist and the coach has defined scouting criteria (position, playing style, budget)  
* **Main Flow**:   
  1. The coach accesses the Talent Scout interface and inputs search criteria  
  2. The system activates the Talent Scouting Agent  
  3. The agent searches player databases and ranks candidates based on tactical fit and statistical compatibility  
  4. The system generates a candidate report with comparative analytics  
  5. The coach reviews the recommendations  
* **Post-condition**: The coach receives data-driven recruitment suggestions aligned with club profile

---

### **UC7 – View Coaching Dashboard and Match History** {#uc7-–-view-coaching-dashboard-and-match-history}

* **Actor**: Coach  
* **Pre-condition**: At least one match analysis session exists in the database  
* **Main Flow**:   
  1. The coach navigates to the main coaching dashboard  
  2. The system aggregates and displays squad performance summaries, tactical trends, and key insights  
  3. The coach accesses the match history section  
  4. The system retrieves past analyzed matches and visualizes longitudinal performance trends  
* **Post-condition**: The coach can view comprehensive squad intelligence and track development over time

### 

### **3.3.2 Non-Functional Requirements** {#3.3.2-non-functional-requirements}

These requirements define measurable quality attributes for system performance, usability, and architecture.

---

#### **3.3.2.1 Performance Requirements**

* **NFR-P1 (Video Processing)**: The CV pipeline must process a 10-minute match clip within **3-5 minutes** on standard hardware  
* **NFR-P2 (Dashboard Responsiveness)**: Dashboard and visualizations must render within **2-3 seconds**  
* **NFR-P3 (AI Coach Response)**: Chat responses must be generated within **5-10 seconds** for standard queries  
* **NFR-P4 (Agent Processing)**: Opponent and scout agents should produce reports within **10-15 minutes**

---

#### **3.3.2.2 Usability Requirements**

* **NFR-U1 (Intuitive Interface)**: Core features must be navigable with **less than 15 minutes** of onboarding  
* **NFR-U2 (Clear Visualizations)**: Tactical displays must use intuitive color schemes with clear legends  
* **NFR-U3 (Natural Language)**: AI coach must accept conversational queries without rigid syntax  
* **NFR-U4 (Actionable Feedback)**: System messages must use coach-friendly language, avoiding technical jargon

---

#### **3.3.2.3 Scalability Requirements**

* **NFR-S1 (Modular Architecture)**: Components must be loosely coupled with well-defined APIs  
* **NFR-S2 (Extensible Data Model)**: Database schema must support adding new metrics without major refactoring  
* **NFR-S3 (Agent Framework)**: Multi-agent system must allow new agents to be added via plug-and-play design  
* **NFR-S4 (Code Quality)**: Code shall follow clean architecture patterns with clear separation of concerns

## **3.4 High-Level System Architecture** {#3.4-high-level-system-architecture}

Following the detailed definition of functional and non-functional requirements, it is essential to visualize how these components interact within the technical infrastructure. The high-level system architecture provides a structural view of the solution, delineating the data flow between the user interface, the backend processing services, the AI/ML processing layer, and the data storage infrastructure.  
*Figure 3 System Architecture*

![][image4]  
**Figure 3** illustrates this architecture, organizing the system into **five distinct layers**: **User Layer**, **Frontend Layer**, **Backend Services**, **AI/ML Processing**, and **Data Storage**. This modular design ensures that computationally intensive tasks—specifically the computer vision pipeline and AI agent analysis—are decoupled from real-time user interactions. By separating the processing engines from the user-facing dashboard, the architecture guarantees a seamless coaching experience, allowing coaches to access squad intelligence and tactical insights immediately while complex video analysis and agent operations run asynchronously in the background.  
The architecture follows a **service-oriented approach** where each backend service (Squad Management, Video Processing, AI Coach, Agent Orchestrator) operates independently and communicates through a centralized API Gateway. This design enables parallel development of system components and facilitates future extensibility, such as adding new AI agents or integrating external data sources, without requiring modifications to the core platform infrastructure.

## **3.5 project timeline**  {#3.5-project-timeline}

![][image5]  
*Figure 4 Project Plan*

## **3.6 Conclusion** {#3.6-conclusion}

This chapter has successfully translated the project’s high-level objectives into a concrete technical specification. By conducting a thorough requirements elicitation process, we identified the critical features necessary to bridge the gap between amateur players and elite coaching analytics.  
The functional requirements established the core capabilities of the system ranging from the automated computer vision pipeline to the interactive AI coach while the non-functional requirements defined the essential quality constraints regarding performance, security, and scalability. Furthermore, the detailed use case modeling **(Figure 2\)** and the high-level system architecture **(Figure 3\)** have provided a structural blueprint for the solution, clarifying how distinct modules will interact to deliver real-time insights.  
With the system’s scope and architectural framework now fully defined, the project is ready to move from the analysis phase to the detailed design and implementation phase, which will be the focus of the subsequent chapters.

# **References** {#references}

| \[1\]  | K. Takumi, T. Kumakura and Y. Akira, "ASPERA: Action SPotting thrEe-modal Recognition Architecture," in *Proceedings of the 20th International Conference on Computer Vision Theory and Applications (VISAPP 2025\)*, Rome, 2025\.  |
| :---- | :---- |
| \[2\]  | S. Gautam, C. Midoglu, V. Thambawita, M. A. Riegler, P. Halvorsen and M. Shah, "SoccerChat: Integrating Multimodal Data for Enhanced Soccer Game Understanding," 01 01 2025\. \[Online\]. Available: https://arxiv.org/html/2505.16630v1?. \[Accessed 23 10 2025\]. |
| \[3\]  | C. M. V. T. M. A. R. P. H. M. S. S. Gautam, "SoccerChat: Integrating Multimodal Data for Enhanced Soccer Game Understanding," 22 May 2025\. \[Online\]. Available: https://arxiv.org/abs/2505.16630?. \[Accessed 20 10 2025\]. |
| \[4\]  | R. Kenny, M. Elez, A. Clansey, N. Virji-Babul and L. Wu, “Individualized monitoring of longitudinal heading exposure in soccer,” *Journal Name,* 20 1 2024\.  |
| \[5\]  | A. Cemek, A. Skripnikov and D. Gillman, "Statistical Adjustment for Tactical Choices When Evaluating Team’s Offensive Output Across Five Major European Club Soccer Leagues," *The Open Sports Sciences Journal,* 10 January 2025\.  |
| \[6\]  | Catapult, "Video Analysis in Football: Enhance Game Tactics," Catapult, 08 01 2025\. \[Online\]. Available: https://www.catapult.com/blog/video-analysis-in-football?. \[Accessed 20 10 2025\]. |
| \[7\]  | N. George, "How to implement video analysis in an amateur football club: TWL Elektra case study," zone14, 12 01 2024\. \[Online\]. Available: https://zone14.ai/en/blog/use-case-football-video-analysis/?. \[Accessed 19 10 2025\]. |
| \[8\]  | Athletes Untapped, “The Average Cost of Private Sports Coaching,” Athletes Untapped, \[Online\]. Available: https://athletesuntapped.com/blog/the-average-cost-of-private-sports-coaching/?. \[Accessed 21 10 2025\]. |

 