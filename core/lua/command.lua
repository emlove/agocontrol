for key,value in pairs(content) do print(key,value) end
if content.subject == "event.environment.timechanged" then
	if content.hour == 0 and content.minute == 39 then
		sendMessage('command=on','uuid=1e68018f-e43b-4279-a314-0a2c0c615d5c')
	end
end
