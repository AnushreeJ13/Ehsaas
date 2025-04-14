// Using the compat version of Firebase
// You shouldn't mix import syntax with the compat version

// Option 1: Change to use Firebase compat properly
const db = firebase.firestore();

// Function to add a document (instead of using addDoc)
function addSession(userId, sessionData) {
  return db.collection('users').doc(userId).collection('sessions').add(sessionData);
}

// Function to track user session
function trackUserSession() {
  const user = firebase.auth().currentUser;
  if (!user) return;
  
  const sessionData = {
    startTime: firebase.firestore.FieldValue.serverTimestamp(),
    device: navigator.userAgent,
    platform: navigator.platform
  };
  
  addSession(user.uid, sessionData)
    .then((docRef) => {
      console.log("Session tracked with ID: ", docRef.id);
      // Store session ID to update when user leaves
      sessionStorage.setItem("currentSessionId", docRef.id);
    })
    .catch((error) => {
      console.error("Error tracking session: ", error);
    });
}

// Function to update session when user leaves
function updateSessionEnd() {
  const user = firebase.auth().currentUser;
  const sessionId = sessionStorage.getItem("currentSessionId");
  
  if (!user || !sessionId) return;
  
  db.collection('users').doc(user.uid).collection('sessions').doc(sessionId).update({
    endTime: firebase.firestore.FieldValue.serverTimestamp()
  }).catch((error) => {
    console.error("Error updating session end time: ", error);
  });
}

// Listen for auth state changes
firebase.auth().onAuthStateChanged((user) => {
  if (user) {
    // User is signed in
    trackUserSession();
    sessionStorage.setItem("isLoggedIn", "true");
  } else {
    // User is signed out
    updateSessionEnd();
    sessionStorage.removeItem("isLoggedIn");
  }
});

// Track when user leaves the page
window.addEventListener('beforeunload', () => {
  updateSessionEnd();
});

// Expose any functions you need to call from other scripts
window.sessionTracker = {
  trackUserSession,
  updateSessionEnd
};