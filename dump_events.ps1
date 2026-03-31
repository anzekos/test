Get-WinEvent -FilterHashtable @{LogName='Application'; ProviderName='M-Files*'; Level=2} -MaxEvents 5 -ErrorAction SilentlyContinue | Select-Object TimeCreated, Message | Format-List
