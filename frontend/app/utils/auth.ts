export const TOKEN_KEY="auth_token"

export function setToken(token:string){
    localStorage.setItem(TOKEN_KEY,token)
}

export function getToken():string | null{
    if(typeof window==="undefined") 
    return null
return localStorage.getItem(TOKEN_KEY)
}

export function clearToken(){
    localStorage.removeItem(TOKEN_KEY)
}
export function isLoggedIn():boolean{
    return !!getToken()
}

export function getAuthHeader(){
    const token=getToken()
    if(!token)
        return{}
    return {
        Authorization:`Bearer ${token}`,
    }
}