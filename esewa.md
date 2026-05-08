# eSewa x WWF Hackathon Submission

## 1. Team Information

### Team Name
<Your Team Name>

### Team Members
For each member:

- **Full Name:**  
- **Email:**  
- **Role:** (e.g., ML Engineer, Backend Developer, UI/UX Designer)  
- **Permanent Address:**  
- **Gender:**  

---

## 2. Problem Understanding

### Problem Statement
Fraudulent KYC submissions pose a significant threat to digital platforms. Attackers may use forged documents, stolen identities, or synthetic identities to create accounts. This leads to security risks, financial fraud, and compliance issues.

### Importance of the Problem
- Financial losses due to fraudulent accounts  
- Reduced trust in digital platforms  
- Regulatory and compliance challenges  
- Increased risk of identity theft and misuse  

### Challenges Identified
- Detection of forged or tampered identity documents  
- Identification of stolen or synthetic identities  
- Detection of duplicate identities across accounts  
- Lack of real-time fraud detection during onboarding  

---

## 3. Proposed Solution

### Solution Overview
We propose an AI-powered KYC fraud detection system that analyzes user-submitted identity data during onboarding. The system processes ID documents and selfies, applies multiple detection models, and generates a risk score to determine whether the account should be approved, flagged, or rejected.

### Key Features
- Face Matching (Selfie vs ID)
- Liveness Detection
- Document Forgery Detection
- OCR-based Data Extraction
- Duplicate Identity Detection
- Device Fingerprinting
- Risk Scoring Engine

### Innovation / Uniqueness
- Multi-layer fraud detection combining multiple signals  
- Designed for low-resource and real-world environments  
- Real-time decision-making with minimal user friction  

---

## 4. Scope of the Solution

### In-Scope
- KYC verification during onboarding  
- Detection of fraudulent identity submissions  
- Risk scoring and automated decision-making  

### Out-of-Scope
- Transaction fraud detection  
- Post-login monitoring  
- Manual verification workflows  

---

## 5. User Journey / Flow

### User Flow Description
1. User uploads ID document and selfie  
2. System preprocesses the data  
3. AI models analyze inputs  
4. Risk score is generated  
5. System returns decision (Approve / Review / Reject)  

### Flow Diagram
*(Insert diagram here in final submission)*

---

## 6. Technology Stack

### Frontend
- React / Flutter  
- Camera API for image and video capture  

### Backend
- FastAPI / Node.js  
- REST API architecture  

### Machine Learning
- Face recognition models (e.g., DeepFace / FaceNet)  
- CNN models for document forgery detection  
- Liveness detection using OpenCV / MediaPipe  

### Database
- PostgreSQL (structured data)  
- MongoDB (images and logs)  

### APIs and Tools
- OCR (Tesseract / EasyOCR)  
- Device fingerprinting tools  
- Image processing libraries (OpenCV)  

---

## 7. System Architecture

### Overview
The system consists of frontend, backend, and ML components. User data flows from the frontend to backend services, where it is processed by ML models. The results are aggregated into a risk score, which determines the final decision.

### Architecture Diagram
*(Insert architecture diagram here)*

---

## 8. Risk Scoring Mechanism

### Scoring Logic
The system calculates a risk score based on:
- Face similarity score  
- Document authenticity score  
- Duplicate identity detection  
- Device anomaly signals  

Each factor contributes to the final score using weighted logic.

### Decision Thresholds
- **Low Risk:** Automatic Approval  
- **Medium Risk:** Manual Review  
- **High Risk:** Rejection  

---

## 9. UI/UX Design

### Wireframes
*(Insert UI sketches or screenshots here)*

### Design Considerations
- Simple and intuitive interface  
- Mobile-friendly design  
- Support for low-bandwidth environments  
- Minimal onboarding friction  

---

## 10. Expected Impact

- Reduction in fraudulent account creation  
- Improved onboarding security  
- Increased user trust  
- Better regulatory compliance  

---

## 11. Limitations

- Limited training dataset  
- Model accuracy may vary  
- Prototype-level implementation  

---

## 12. Future Improvements

- Integration with national identity databases  
- Advanced behavioral biometrics  
- Real-time fraud monitoring  

---

## 13. Conclusion

This project presents a practical and scalable solution for detecting fraudulent KYC submissions. By combining multiple AI-based techniques with a structured risk scoring system, it enhances security while maintaining a smooth user onboarding experience.