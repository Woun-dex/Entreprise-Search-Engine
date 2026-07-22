import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        repo_info_url = "https://api.github.com/repos/tssovi/grokking-the-object-oriented-design-interview"
        r1 = await client.get(repo_info_url)
        print(f"Repo info: {r1.status_code} {r1.reason_phrase}")
        if r1.status_code != 200:
            print(r1.text)

        url = "https://api.github.com/repos/tssovi/grokking-the-object-oriented-design-interview/git/trees/master?recursive=1"
        r2 = await client.get(url)
        print(f"Tree info: {r2.status_code} {r2.reason_phrase}")
        if r2.status_code != 200:
            print(r2.text)

asyncio.run(main())
