# import pygal library
import pygal
  
# create a world map
worldmap =  pygal.maps.world.World()
  
# set the title of the map
#worldmap.title = 'Countries'
  
# adding the countries
worldmap.add('members', {
        'cn' : 1,
        'in' : 2,
        'gr' : 1,
        'pk' : 2,
        'it' : 9,
        'mx' : 3,
        'gb' : 1,
        'de' : 1,
        'tr' : 3,
        'fr' : 1,
        'ch' : 1,
        'cl' : 1,
        'ar' : 1,
        'hr' : 1
})
  
# save into the file
worldmap.render_to_file('abc.svg')
  
print("Success")