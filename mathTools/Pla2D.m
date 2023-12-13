%fem net
clf
% definim un gràfic 2D per representar els quatre quadrants del pla
a=-10;
b=10;
x=(b-a).*rand(50,1)+a;
y=(b-a).*rand(50,1)+a;
%c=y
scatter(x,y); % fem un conjunt de punts il·lustratius

% afegim text als llocs adient
xlabel('x, abcisses');
ylabel('y, ordenades');
grid on;
set(gca,'XAxisLocation','origin','YAxisLocation','origin');

% creem anotacions als quatre quadrants
mida = [0.1 0.3];
dimq1 = [.7 .5 mida];
strq1 = "Quadrant 1";
annotation('textbox',dimq1,'String',strq1,'FitBoxToText','on')
dimq2 = [.2 .5 mida];
strq2 = "Quadrant 2";
annotation('textbox',dimq2,'String',strq2,'FitBoxToText','on');
dimq3 = [.2 .0 mida];
strq3 = "Quadrant 3";
annotation('textbox',dimq3,'String',strq3,'FitBoxToText','on');
dimq4 = [.7 .0 mida];
strq4 = "Quadrant 4";
annotation('textbox',dimq4,'String',strq4,'FitBoxToText','on');

%gravem figura en format PNG
saveas(gcf,'Pla2D.png')