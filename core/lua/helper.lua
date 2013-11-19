function tprint (tbl, indent)
  if not indent then indent = 0 end
  for k, v in pairs(tbl) do
    formatting = string.rep("  ", indent) .. k .. ": "
    if type(v) == "table" then
      print(formatting)
      tprint(v, indent+1)
    else
      print(formatting .. tostring(v))
    end
  end
end

function getdevicename (deviceuuid)
  for k, v in pairs(inventory.devices) do
    if k == deviceuuid then
      return v.name
    end
  end
end

