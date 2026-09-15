
import { initializeApp } from "https://www.gstatic.com/firebasejs/12.19.0/firebase-app.js";

import {
    getAuth,
    GoogleAuthProvider,
    signInWithPopup,
    createUserWithEmailAndPassword,
    signInWithEmailAndPassword,
    sendPasswordResetEmail,
    onAuthStateChanged,
    signOut
} from "https://www.gstatic.com/firebasejs/12.19.0/firebase-auth.js";


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


const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

auth.useDeviceLanguage();

const googleProvider = new GoogleAuthProvider();
googleProvider.setCustomParameters({
    prompt: "select_account"
});


function showMessage(text, type = "info") {
    const element = document.getElementById("message");

    if (!element) return;

    element.textContent = text;
    element.className = `message ${type}`;
}


async function goToAI(user) {
    try {
        const token = await user.getIdToken(true);

        const response = await fetch("/api/account/me", {
            method: "GET",
            headers: {
                Authorization: `Bearer ${token}`
            }
        });

        const data = await response.json();

        if (!response.ok || !data.ok) {
            throw new Error(
                data.error || "Server authentication failed"
            );
        }

        window.location.href = "/miniapp/ai";

    } catch (error) {
        console.error(error);

        showMessage(
            "Ошибка проверки аккаунта на сервере.",
            "error"
        );
    }
}


const googleButton =
    document.getElementById("googleLogin");

if (googleButton) {
    googleButton.addEventListener("click", async () => {
        try {
            showMessage("Открываем Google...", "info");

            const result = await signInWithPopup(
                auth,
                googleProvider
            );

            await goToAI(result.user);

        } catch (error) {
            console.error(error);

            showMessage(
                error.message || "Ошибка Google авторизации",
                "error"
            );
        }
    });
}


const loginButton =
    document.getElementById("emailLogin");

if (loginButton) {
    loginButton.addEventListener("click", async () => {
        const email =
            document.getElementById("email")
                .value.trim();

        const password =
            document.getElementById("password")
                .value;

        if (!email || !password) {
            showMessage(
                "Введите Email и пароль.",
                "error"
            );
            return;
        }

        try {
            showMessage("Вход...", "info");

            const result =
                await signInWithEmailAndPassword(
                    auth,
                    email,
                    password
                );

            await goToAI(result.user);

        } catch (error) {
            console.error(error);

            showMessage(
                "Не удалось войти. Проверь Email и пароль.",
                "error"
            );
        }
    });
}


const registerButton =
    document.getElementById("register");

if (registerButton) {
    registerButton.addEventListener("click", async () => {
        const email =
            document.getElementById("email")
                .value.trim();

        const password =
            document.getElementById("password")
                .value;

        if (!email || !password) {
            showMessage(
                "Введите Email и пароль.",
                "error"
            );
            return;
        }

        if (password.length < 6) {
            showMessage(
                "Пароль должен содержать минимум 6 символов.",
                "error"
            );
            return;
        }

        try {
            showMessage("Создаём аккаунт...", "info");

            const result =
                await createUserWithEmailAndPassword(
                    auth,
                    email,
                    password
                );

            await goToAI(result.user);

        } catch (error) {
            console.error(error);

            showMessage(
                error.message || "Не удалось создать аккаунт.",
                "error"
            );
        }
    });
}


const resetButton =
    document.getElementById("resetPassword");

if (resetButton) {
    resetButton.addEventListener("click", async () => {
        const email =
            document.getElementById("email")
                .value.trim();

        if (!email) {
            showMessage(
                "Сначала введи Email.",
                "error"
            );
            return;
        }

        try {
            await sendPasswordResetEmail(
                auth,
                email
            );

            showMessage(
                "Письмо для сброса пароля отправлено.",
                "success"
            );

        } catch (error) {
            console.error(error);

            showMessage(
                "Не удалось отправить письмо.",
                "error"
            );
        }
    });
}


window.TigranAuth = {
    auth,

    async token() {
        if (!auth.currentUser) {
            return null;
        }

        return await auth.currentUser.getIdToken();
    },

    async logout() {
        await signOut(auth);

        window.location.href =
            "/miniapp/login";
    }
};


onAuthStateChanged(auth, (user) => {
    console.log(
        user
            ? `Firebase user: ${user.uid}`
            : "Firebase user: signed out"
    );
});
