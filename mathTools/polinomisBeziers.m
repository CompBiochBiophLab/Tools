%Exercici Splines Beziers
% Treballarem amb l'operador simbòlic i la variable 
% serà el paràmetre t, que varia entre 0 i 1, els 
% dos punts entre els quals interpolem
syms t

% Construïm els polinomis
t1 = -t^3+3*t^2-3*t+1
t2 = 3*t^3-6*t^2+3*t
t3 = -3*t^3+3*t^2
t4 = t^3

% Determinem les coordenades
x = [1 2 3 4]
y = [2 5 7 3]
scatter(x,y,'d'),hold on

% Cadascun dels supòsits de l'exercici 
% beziers a
polx = 1*t1+2*t2+3*t3+4*t4
poly = 2*t1+5*t2+7*t3+3*t4
fplot(polx,poly,[0 1]), hold on

% beziers b
polx = 1*t1+2*t2+4*t3+3*t4
poly = 2*t1+5*t2+3*t3+7*t4
fplot(polx,poly,[0 1]), hold on

% beziers c
polx = 3*t1+1*t2+2*t3+4*t4
poly = 7*t1+2*t2+5*t3+3*t4
fplot(polx,poly,[0 1]), hold on

% beziers d
polx = 2*t1+1*t2+4*t3+3*t4
poly = 5*t1+2*t2+3*t3+7*t4
fplot(polx,poly,[0 1]), hold off