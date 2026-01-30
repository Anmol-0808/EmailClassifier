import Link from "next/link"

export default function Home(){
  return(
    <main style={{padding:"40px"}}>
      <h1>MailMind</h1>
      <Link href="/login">
      Go to Login
      </Link>
    </main>
  )
}