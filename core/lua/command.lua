for key,value in pairs(content) do print(key,value) end
for key,value in pairs(inventory.devices) do
	print (key,value)
	for key2,value2 in pairs (value) do
		print (key2,value2)
	end
	for key2,value2 in pairs (value.values) do
		print (key2,value2)
		for key3,value3 in pairs (value2) do
			print (key3,value3)
		end
	end
end
if content.subject == "event.environment.timechanged" then
	if content.hour == 0 and content.minute == 39 then
		sendMessage('command=on','uuid=1e68018f-e43b-4279-a314-0a2c0c615d5c')
	end
end
