import { initializeApp } from
    "https://www.gstatic.com/firebasejs/12.19.0/firebase-app.js";

import {
    getAuth,
    onAuthStateChanged
} from
    "https://www.gstatic.com/firebasejs/12.19.0/firebase-auth.js";


/*
    СЮДА СКОПИРУЙ firebaseConfig
    ИЗ ТВОЕГО firebase-auth.js
*/
const firebaseConfig = {
    apiKey: "AIzaSyDVr7YpqYyleoBNpfl1QQc0IMRQRYAIr8M",
    authDomain: "yourtigranmods-papaji-devffsrc.firebaseapp.com",
    databaseURL: "https://yourtigranmods-papaji-devffsrc-default-rtdb.firebaseio.com",
    projectId: "yourtigranmods-papaji-devffsrc",
    storageBucket: "yourtigranmods-papaji-devffsrc.firebasestorage.app",
    messagingSenderId: "190570756810",
    appId: "1:190570756810:web:7839bf4a545c51d7b19233",
    measurementId: "G-729S4RCQK4"
};


document.documentElement.style.visibility =
    "hidden";


const app = initializeApp(
    firebaseConfig,
    "tigran-auth-guard"
);

const auth = getAuth(app);


onAuthStateChanged(
    auth,
    user => {

        if (!user) {

            window.location.replace(
                "/miniapp/login"
            );

            return;
        }

        document.documentElement.style.visibility =
            "visible";

        window.TigranCurrentUser = user;
    }
);
