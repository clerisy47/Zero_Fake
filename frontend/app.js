const samplePayload = {
  submission_id: "sub-2001",
  channel: "web",
  claimed_country: "Nepal",
  gateway: {
    tls_valid: true,
    ip_requests_last_minute: 6,
    device_requests_last_minute: 2,
    session_token_valid: true,
  },
  device: {
    device_id: "dev-q1",
    known_recent_submission_count: 1,
    user_agent: "Mozilla/5.0",
    os_family: "iOS",
  },
  network: {
    ip: "103.40.1.10",
    is_vpn: false,
    is_tor: false,
    is_datacenter_proxy: false,
    country: "Nepal",
    asn_type: "retail",
  },
  behavior: {
    form_completion_seconds: 72,
    copy_paste_events: 0,
    typing_interval_stddev_ms: 230,
    mouse_path_entropy: 0.61,
  },
  document: {
    document_type: "passport",
    issuing_country: "Nepal",
    document_number: "NEP-987654-10",
    full_name: "Sita Poudel",
    dob: "1990-06-11",
    claimed_age: 35,
    expiry: "2031-06-11",
    ela_score: 0.1,
    font_match_score: 0.93,
    mrz_checksum_valid: true,
    template_match_score: 0.95,
    image_quality_score: 0.9,
  },
  biometric: {
    liveness_score: 0.91,
    face_similarity_score: 0.88,
    deepfake_score: 0.08,
    camera_injection_detected: false,
    estimated_age: 34,
  },
};

let endpoint = "http://127.0.0.1:8000/kyc/submit";

const submissionJson = document.getElementById("submissionJson");
const submitBtn = document.getElementById("submitBtn");
const loadSampleBtn = document.getElementById("loadSample");
const resultOutput = document.getElementById("resultOutput");
const statusBadge = document.getElementById("statusBadge");

const submissionJson2 = document.getElementById("submissionJson2");
const submitBtn2 = document.getElementById("submitBtn2");
const loadSampleBtn2 = document.getElementById("loadSample2");
const resultOutput2 = document.getElementById("resultOutput2");
const statusBadge2 = document.getElementById("statusBadge2");

const samplePayloadDocs = document.getElementById("samplePayloadDocs");

const pages = {
  home: document.getElementById("home-page"),
  submit: document.getElementById("submit-page"),
  docs: document.getElementById("docs-page"),
  about: document.getElementById("about-page"),
};

function showPage(pageName) {
  Object.values(pages).forEach(page => page.classList.remove("active"));
  pages[pageName].classList.add("active");
}

function setResult(status, payload, isSecond = false) {
  const badge = isSecond ? statusBadge2 : statusBadge;
  const output = isSecond ? resultOutput2 : resultOutput;
  badge.textContent = status;
  if (status.toLowerCase().includes("error")) {
    badge.style.background = "#ffe3db";
    badge.style.color = "#7a3b24";
  } else {
    badge.style.background = "#dfe9e1";
    badge.style.color = "#2d4732";
  }
  output.textContent = typeof payload === "string" ? payload : JSON.stringify(payload, null, 2);
}

function loadSample(isSecond = false) {
  const jsonArea = isSecond ? submissionJson2 : submissionJson;
  jsonArea.value = JSON.stringify(samplePayload, null, 2);
  setResult("Sample loaded", "You can edit the JSON or submit as-is.", isSecond);
}

async function submitKyc(isSecond = false) {
  try {
    const jsonArea = isSecond ? submissionJson2 : submissionJson;
    const body = JSON.parse(jsonArea.value);
    setResult("Submitting…", "Waiting for response...", isSecond);

    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    const responseBody = await response.json();

    if (!response.ok) {
      throw new Error(responseBody.detail || response.statusText || "Unknown error");
    }

    setResult("Success", responseBody, isSecond);
  } catch (error) {
    setResult("Error", error.message || "Unable to submit request.", isSecond);
  }
}

async function checkServerStatus() {
  try {
    const healthEndpoint = endpoint.replace("/kyc/submit", "/health");
    const response = await fetch(healthEndpoint);
    if (response.ok) {
      return "Server is running";
    } else {
      return "Server not responding";
    }
  } catch (error) {
    return "Server not reachable";
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  // Navigation
  document.querySelectorAll(".nav-links a").forEach(link => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      const page = e.target.getAttribute("data-page");
      showPage(page);
    });
  });

  // Home page events
  loadSampleBtn.addEventListener("click", () => loadSample(false));
  submitBtn.addEventListener("click", () => submitKyc(false));

  // Submit page events
  loadSampleBtn2.addEventListener("click", () => loadSample(true));
  submitBtn2.addEventListener("click", () => submitKyc(true));

  // Load sample on page load
  loadSample(false);
  loadSample(true);

  // Load sample payload in docs
  samplePayloadDocs.textContent = JSON.stringify(samplePayload, null, 2);

  // Check server status
  const serverStatus = await checkServerStatus();
  console.log("Server status:", serverStatus);
  // You can display this in the UI if needed
});

window.addEventListener("load", () => showPage("home"));
