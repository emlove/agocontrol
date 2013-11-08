x=sendMessage('command=on','uuid=12345')
print ('call from lua result:',x)
print ('event name:',content['event'])
for key,value in pairs(content) do print(key,value) end
