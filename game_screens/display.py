# Source - https://stackoverflow.com/a/64990819
# Posted by Rabbid76, modified by community. See post 'Timeline' for change history
# Retrieved 2026-02-14, License - CC BY-SA 4.0

def button(x, y, w, h, img, imgon, action=None):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()

    rect = pygame.Rect(x, y, w, h)
    on_button = rect.collidepoint(mouse)
    pygame.draw.rect(screen, rect)
    screen.blit(img, img.get_rect(center = rect.center))


image = pygame.image.load('../assets/Typo-buttons/left.png').convert_alpha()
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()

    screen.blit(randomList, [0, 0])
    button(399, 390, 300, 50, image)
    pygame.display.update()
