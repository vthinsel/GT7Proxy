import sys
from granturismo import Feed
import matplotlib.pyplot as plt

if __name__ == '__main__':
  ip_address = sys.argv[1]

  # setup the plot styling
  plt.ion() # allows us to continue to update the plot
  fig, ax = plt.subplots(figsize=(8, 8))
  ax.axis('off') # hides the black border around the axis.
  plt.xticks([])
  plt.yticks([])

  # this will be the previous x and z points. We don't want to re-plot all our points because 
  # that'll be too slow and the graph cant keep up with our stream. We're only gonna plot the newest segment.
  px, pz = None, None

  count = 0
  with Feed(ip_address) as feed:
    while True:
      count += 1
      # only update graph every 10th of a second just cuz it doesn't matter for us, and it's easier on the computer
      # but we still need to grab the packet even if we're not using it
      packet = feed.get()

      # note, we're negating z so the map will appear int he same orientation as it does in the game's minimap
      x, z = packet.position.x, -packet.position.z
      if px is None:
        px, pz = x, z
        continue

      # here we're getting the ratio of how fast the car's going compared to it's max speed.
      # we're multiplying by 3 to boost the colorization range.
      speed = min(1, packet.car_speed / packet.car_max_speed) * 3
      # Now use the "speed" ratio to select the color from the Matplotlib pallet
      color = plt.cm.plasma(speed)

      # plot the current step
      plt.plot([px, x], [pz,  z], color=color)

      # set the aspect ratios to be equal for x/z axis, this way the map doesn't look skewed
      plt.gca().set_aspect('equal', adjustable='box')

      # pause for a freakishly shot amount of time. We need a pause so that it'll trigger a graph update
      plt.pause(0.00000000000000000001)

      # set the previous (x, z) to the current (x, z)
      px, pz = x, z