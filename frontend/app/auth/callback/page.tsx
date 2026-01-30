"use client"

import { useEffect } from "react"
import { useSearchParams,useRouter } from "next/navigation"
import { setToken } from "@/app/utils/auth"

export default function AuthCallBackPage(){
    const searchParams=useSearchParams()
    const router=useRouter()


useEffect(()=>{
    const token =searchParams.get("token")
    if(token){
        setToken(token)
        router.push("/dashboard")
    }
        else{
            router.push("/login")
        }},[searchParams,router])
        return <p>Logging you in...</p>
    
}