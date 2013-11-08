x=sendMessage('message')
print ('call from lua result:',x)
print ('event name:',content['event'])
for key,value in pairs(content) do print(key,value) end
