"use client";

export default function LoginPage(){
    const handleLogin=()=>{
        window.location.href=
        "http://localhost:8000/auth/google/login"
    }


return (
    <div style={{padding:"40px"}}>
        <h1>Login</h1>
        <button onClick={handleLogin}>
        Continue with Google
        </button>
    </div>
)
}